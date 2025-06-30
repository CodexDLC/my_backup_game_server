# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_1lvl/equipment_template_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func # Добавлен func для count

# Импорт модели EquipmentTemplate
from game_server.database.models.models import EquipmentTemplate

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class EquipmentTemplateRepositoryImpl(IEquipmentTemplateRepository):
    """
    Репозиторий для управления объектами EquipmentTemplate в базе данных (асинхронный).
    Реализует интерфейс IEquipmentTemplateRepository.
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory
        logger.debug("EquipmentTemplateRepositoryImpl инициализирован с db_session_factory.")

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает новый шаблон предмета снаряжения.
        """
        async with await self._get_session() as session:
            new_template = EquipmentTemplate(**data)
            session.add(new_template)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Шаблон предмета снаряжения '{new_template.item_code}' создан.")
                return new_template
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании шаблона '{data.get('item_code', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Шаблон с таким кодом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании шаблона '{data.get('item_code', 'N/A')}': {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[EquipmentTemplate]:
        """
        Получает шаблон по его числовому идентификатору (id).
        """
        async with await self._get_session() as session:
            stmt = fselect(EquipmentTemplate).where(EquipmentTemplate.id == id) # Предполагается наличие поля 'id'
            result = await session.execute(stmt)
            return result.scalar_one_or_none()


    async def get_by_item_code(self, item_code: str) -> Optional[EquipmentTemplate]:
        """
        Получает шаблон по его item_code.
        """
        async with await self._get_session() as session:
            stmt = fselect(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_all_item_codes(self) -> List[str]:
        """
        Получает все item_code существующих шаблонов предметов снаряжения.
        """
        async with await self._get_session() as session:
            stmt = fselect(EquipmentTemplate.item_code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all(self) -> List[EquipmentTemplate]:
        """
        Получает все шаблоны предметов снаряжения.
        Соответствует методу get_all интерфейса.
        """
        async with await self._get_session() as session:
            stmt = fselect(EquipmentTemplate)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_templates(self) -> List[EquipmentTemplate]:
        """
        Получает все шаблоны предметов снаряжения.
        (Этот метод не был в интерфейсе, но может быть полезен. Оставляем.)
        """
        return await self.get_all() # Переиспользуем get_all, чтобы избежать дублирования логики

    async def update(self, item_code: str, updates: Dict[str, Any]) -> Optional[EquipmentTemplate]:
        """
        Обновляет существующий шаблон по его item_code.
        """
        async with await self._get_session() as session:
            stmt = update(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code).values(**updates).returning(EquipmentTemplate)
            result = await session.execute(stmt)
            updated_template = result.scalars().first()
            if updated_template:
                await session.commit()
                logger.info(f"Шаблон (item_code: {item_code}) обновлен.")
            else:
                await session.rollback()
                logger.warning(f"Шаблон с item_code {item_code} не найден для обновления.")
            return updated_template

    async def delete(self, id: int) -> bool:
        """
        Удаляет шаблон по его числовому идентификатору (id).
        """
        async with await self._get_session() as session:
            stmt = delete(EquipmentTemplate).where(EquipmentTemplate.id == id) # Предполагается наличие поля 'id'
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.commit()
                logger.info(f"Шаблон (ID: {id}) удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Шаблон с ID {id} не найден для удаления.")
                return False

    async def delete_by_item_code(self, item_code: str) -> bool:
        """
        Удаляет шаблон по его item_code.
        """
        async with await self._get_session() as session:
            stmt = delete(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.commit()
                logger.info(f"Шаблон (item_code: {item_code}) удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Шаблон с item_code {item_code} не найден для удаления.")
                return False

    async def delete_by_item_code_batch(self, item_codes: List[str]) -> int:
        """
        Массово удаляет шаблоны по списку item_code.
        """
        if not item_codes:
            logger.info("Пустой список item_codes для массового удаления. Ничего не сделано.")
            return 0
        
        async with await self._get_session() as session:
            try:
                # Используем оператор in_() для удаления нескольких записей одним запросом
                stmt = delete(EquipmentTemplate).where(EquipmentTemplate.item_code.in_(item_codes))
                result = await session.execute(stmt)
                deleted_count = result.rowcount
                await session.commit()
                logger.info(f"Массовое удаление шаблонов завершено. Удалено {deleted_count} записей.")
                return deleted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка при массовом удалении шаблонов по item_code: {e}", exc_info=True)
                raise


    async def upsert(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает или обновляет шаблон. Если шаблон с данным item_code существует,
        он обновляется; иначе создается новый.
        """
        item_code = data.get("item_code")
        if not item_code:
            raise ValueError("Item code must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
                insert_stmt = pg_insert(EquipmentTemplate).values(**data)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[EquipmentTemplate.item_code],
                    set_={
                        "display_name": insert_stmt.excluded.display_name,
                        "category": insert_stmt.excluded.category,
                        "sub_category": insert_stmt.excluded.sub_category,
                        "equip_slot": insert_stmt.excluded.equip_slot,
                        "inventory_size": insert_stmt.excluded.inventory_size,
                        "material_code": insert_stmt.excluded.material_code,
                        "suffix_code": insert_stmt.excluded.suffix_code,
                        "base_modifiers_json": insert_stmt.excluded.base_modifiers_json,
                        "quality_tier": insert_stmt.excluded.quality_tier,
                        "rarity_level": insert_stmt.excluded.rarity_level,
                        "icon_url": insert_stmt.excluded.icon_url,
                        "description": insert_stmt.excluded.description,
                    }
                ).returning(EquipmentTemplate)

                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_template = result.scalar_one_or_none()
                if not upserted_template:
                    raise RuntimeError("UPSERT шаблона не вернул объект.")
                logger.info(f"Шаблон '{item_code}' успешно добавлен/обновлен.")
                return upserted_template
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT шаблона '{item_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении шаблона: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT шаблона '{item_code}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет шаблоны.
        Если шаблон с данным item_code существует, он обновляется; иначе создается новый.
        """
        if not data_list:
            logger.info("Пустой список данных для upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
                updatable_fields = {
                    k: pg_insert(EquipmentTemplate).excluded[k]
                    for k in EquipmentTemplate.__table__.columns.keys()
                    if k not in ['item_code']
                }
                
                insert_stmt = pg_insert(EquipmentTemplate).values(data_list)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[EquipmentTemplate.item_code],
                    set_=updatable_fields
                )
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} шаблонов предметов.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT шаблонов предметов: {e}", exc_info=True)
                raise
