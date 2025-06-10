# game_server/utils/load_seeds/seed_loader.py

import json
import os
import uuid
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Type
from sqlalchemy import UUID, inspect, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.yaml_readers import YamlReader
from game_server.database.models.models import Base
from game_server.services.logging.logging_setup import logger

from .seeds_config import SeedsConfig

class SeedLoader:
    def __init__(self, session: AsyncSession):
        self.session = session
        logger.info("✅ SeedLoader инициализирован")

    async def load_yaml_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        try:
            logger.debug(f"📂 Загружаем YAML: {file_path}")
            with open(str(file_path), 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)
                logger.debug(f"🔍 Загружены данные из YAML '{file_path}': тип: {type(loaded_data)}, ключи: {loaded_data.keys() if isinstance(loaded_data, dict) else 'N/A'}")
                return loaded_data
        except FileNotFoundError:
            logger.warning(f"⚠️ Файл не найден: {file_path}. Пропуск загрузки.")
            return None
        except yaml.YAMLError as e:
            logger.error(f"❌ Ошибка парсинга YAML в файле {file_path}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при загрузке {file_path}: {str(e)}", exc_info=True)
            return None

    async def process_seed_file(self, file_path: Path, model: Type[Base]) -> tuple[int, int]:
        logger.debug(f"📜 Обрабатываем seed-файл: {file_path} ({model.__name__})")

        pk_column_names = [col.name for col in inspect(model).primary_key]
        logger.debug(f"🔍 Первичные ключи для модели {model.__name__}: {pk_column_names}")

        if not pk_column_names:
            logger.error(f"❌ Модель {model.__name__} не имеет первичного ключа. Пропуск файла.")
            return 0, 0
        
        # Получаем имя PK для использования в YamlReader, если формат данных - словарь
        # Используем SeedsConfig.get_pk_column для более точного определения PK
        pk_for_yaml_reader = SeedsConfig.get_pk_column(model) 
        if not pk_for_yaml_reader:
            logger.error(f"❌ Не удалось определить первичный ключ для модели '{model.__name__}'. Пропуск файла.")
            return 0, 0

        # === ИСПРАВЛЕНИЕ: Используем YamlReader для получения items_to_process ===
        items_to_process = await YamlReader.get_items_from_yaml(file_path, pk_for_yaml_reader)
        # === КОНЕЦ ИСПРАВЛЕНИЯ ===

        logger.debug(f"📊 Всего элементов для обработки в файле: {len(items_to_process)}")

        if not items_to_process:
            logger.warning(f"⚠️ Файл {file_path} не содержит валидных данных для обработки. Удаляем все записи для модели {model.__name__}...")
            deleted_count = await self._clear_model_data(model)
            await self.session.commit()
            logger.info(f"✅ Удалено {deleted_count} записей из таблицы {model.__tablename__}.")

        # Условие для очистки таблицы, если items_to_process пусто
        if not items_to_process: # ИСПРАВЛЕНО: Проверяем items_to_process, а не data['data']
            logger.warning(f"⚠️ Файл {file_path} не содержит валидных данных для обработки. Удаляем все записи для модели {model.__name__}...")
            deleted_count = await self._clear_model_data(model)
            await self.session.commit()
            logger.info(f"✅ Удалено {deleted_count} записей из таблицы {model.__tablename__}.")
            return 0, 0

        inserted_count, updated_count = 0, 0

        batch_size = SeedsConfig.BATCH_SIZE
        logger.debug(f"📊 Всего элементов для обработки в файле: {len(items_to_process)}")

        for i in range(0, len(items_to_process), batch_size):
            batch = items_to_process[i:i + batch_size]
            logger.debug(f"📦 Обработка батча {i // batch_size + 1}/{len(items_to_process) // batch_size + (1 if len(items_to_process) % batch_size > 0 else 0)} (размер: {len(batch)})")
            
            batch_values = []
            for item_data in batch:
                missing_pk_keys = [col for col in pk_column_names if col not in item_data]
                if missing_pk_keys:
                    logger.error(f"❌ Ошибка: В элементе отсутствуют ключи первичного ключа {missing_pk_keys} для {model.__name__}! Элемент: {item_data}. Пропуск элемента.")
                    continue
                
                for col in inspect(model).columns:
                    if isinstance(col.type, UUID) and col.name in item_data and isinstance(item_data[col.name], str):
                        try:
                            item_data[col.name] = uuid.UUID(item_data[col.name])
                            logger.debug(f"    🔄 UUID преобразован для {col.name}: {item_data[col.name]}")
                        except ValueError:
                            logger.error(f"Некорректный UUID для {col.name} в {model.__name__}: {item_data[col.name]}. Пропуск элемента.")
                            continue
                batch_values.append(item_data)
            
            logger.debug(f"  📝 Подготовлено batch_values для UPSERT (элементов: {len(batch_values)})")

            # 🔥🔥🔥 НОВЫЙ ЛОГ ДЛЯ ОТЛАДКИ JSONB 🔥🔥🔥
            # Попробуем распечатать содержимое 'items' для StarterInventory
            if model.__name__ == 'CharacterStarterInventory': # Замените на точное имя вашей модели
                for item_val in batch_values:
                    if 'items' in item_val:
                        logger.critical(f"DEBUG_JSONB: 'items' field type is {type(item_val['items'])}, value: {item_val['items']}")
                        # Попробуйте принудительно сериализовать, чтобы увидеть ошибку здесь
                        try:
                            json.dumps(item_val['items'])
                            logger.critical(f"DEBUG_JSONB: 'items' field IS JSON serializable.")
                        except Exception as json_e:
                            logger.critical(f"DEBUG_JSONB: 'items' field IS NOT JSON serializable: {json_e}", exc_info=True)
            # 🔥🔥🔥 КОНЕЦ НОВОГО ЛОГА 🔥🔥🔥

            if not batch_values:
                logger.warning(f"  ⚠️ Батч {i // batch_size + 1} пуст после фильтрации/обработки. Пропуск UPSERT.")
                continue

            try:
                insert_stmt = pg_insert(model).values(batch_values)

                update_cols = {
                    col.name: getattr(insert_stmt.excluded, col.name)
                    for col in model.__table__.columns
                    if col.name not in pk_column_names
                }
                
                if not update_cols:
                    upsert_stmt = insert_stmt.on_conflict_do_nothing(index_elements=pk_column_names)
                    logger.debug(f"  ⚡️ Выполняется UPSERT (DO NOTHING) для {model.__name__} по PK: {pk_column_names}")
                else:
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=pk_column_names,
                        set_=update_cols
                    )
                    logger.debug(f"  ⚡️ Выполняется UPSERT (DO UPDATE) для {model.__name__} по PK: {pk_column_names}, обновляемые поля: {list(update_cols.keys())}")
                
                # ИСПРАВЛЕНИЕ: Удаляем problematic_returning_clause.
                # Просто выполняем UPSERT-запрос без RETURNING для обхода TypeError.
                await self.session.execute(upsert_stmt)
                
                # Поскольку мы не получаем returned_ids, мы не можем точно посчитать updated_count из результата.
                # Увеличиваем updated_count на количество элементов в батче, если предполагаем, что все они успешно обрабатываются.
                updated_count += len(batch_values)
                logger.debug(f"  ✅ UPSERT выполнен для {model.__name__}. Приблизительно затронуто: {len(batch_values)} строк.")

            except IntegrityError as e:
                await self.session.rollback()
                logger.error(f"❌ IntegrityError при UPSERT для {model.__name__}, батч (начало): {batch[0] if batch else 'N/A'}: {e}", exc_info=True)
            except Exception as e:
                await self.session.rollback()
                logger.error(f"❌ Непредвиденная ошибка при UPSERT для {model.__name__}, батч (начало): {batch[0] if batch else 'N/A'}: {e}", exc_info=True)
            
            await self.session.commit()
            logger.debug(f"💾 Коммит данных (батч: {len(batch_values)} записей). Всего обработано: {updated_count}")

        logger.debug(f"✅ Завершена обработка {os.path.basename(file_path)}: {inserted_count} вставлено, {updated_count} обновлено")
        return inserted_count, updated_count

    async def _clear_model_data(self, model: Type[Base]) -> int:
        """НОВАЯ ФУНКЦИЯ: Удаляет все записи из таблицы, соответствующей модели."""
        try:
            result = await self.session.execute(delete(model))
            logger.info(f"🗑️ Удалены все записи из таблицы {model.__tablename__}.")
            return result.rowcount
        except Exception as e:
            logger.error(f"❌ Ошибка при очистке таблицы {model.__tablename__}: {e}", exc_info=True)
            await self.session.rollback() 
            return 0