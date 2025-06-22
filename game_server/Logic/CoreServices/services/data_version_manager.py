# game_server/Logic/InfrastructureLogic/services/data_version_manager.py

import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select, Column, String, Table, MetaData

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# --- Определение таблицы для хранения версий ---
metadata_obj = MetaData()

data_versions_table = Table(
    'data_versions',
    metadata_obj,
    Column('table_name', String, primary_key=True, comment="Имя таблицы или логической группы данных"),
    Column('data_hash', String, nullable=False, comment="Хэш-сумма данных (SHA256)")
)


def _json_serializer_with_uuid(obj):
    """
    Кастомный сериализатор для JSON, который умеет обрабатывать UUID.
    """
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class DataVersionManager:
    """
    Универсальный сервис для управления версиями справочных данных
    в PostgreSQL и кэширования их в Redis.
    """


    @staticmethod
    def _calculate_data_hash(data_list: List[Dict[str, Any]]) -> str:
        """
        Вычисляет SHA256 хэш для списка словарей, представляющих данные.
        Детерминированно сортирует данные перед хэшированием.
        """
        if not data_list:
            return hashlib.sha256(b"").hexdigest()

        try:
            # Преобразуем каждый словарь в JSON-строку, отсортировав ключи, чтобы гарантировать детерминированность
            # UUID объекты будут сериализованы в строки с помощью _json_serializer_with_uuid
            serialized_items = []
            for item in data_list:
                # Гарантируем сортировку ключей словаря для детерминированного JSON
                serialized_item = json.dumps(item, sort_keys=True, default=_json_serializer_with_uuid)
                serialized_items.append(serialized_item)

            # Сортируем список JSON-строк для детерминированного порядка всего списка
            serialized_items.sort()

            # Объединяем все отсортированные JSON-строки в одну большую строку
            combined_string = "".join(serialized_items)

            # 🔥 ДОБАВЛЕНА ЛОГГИРУЮЩАЯ СТРОКА ДЛЯ ДЕБАГА
            # Используйте logger.debug или logger.info, чтобы увидеть эту строку в логах
            logger.debug(f"DEBUG_HASH_STRING for {data_list[0].get('material_code', 'N/A') if data_list else 'N/A'} (first 500 chars): {combined_string[:500]}")
            # Дополнительно можно вывести весь хеш
            # logger.debug(f"DEBUG_HASH_VALUE for {data_list[0].get('material_code', 'N/A') if data_list else 'N/A'}: {hashlib.sha256(combined_string.encode('utf-8')).hexdigest()}")


            return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        except TypeError as e:
            logger.error(f"Ошибка сериализации данных для хэширования: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.critical(f"Критическая ошибка при вычислении хэша данных: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_db_version(session: AsyncSession, table_name: str) -> Optional[str]:
        """Получает текущую хэш-версию для таблицы из БД."""
        try:
            stmt = select(data_versions_table.c.data_hash).where(data_versions_table.c.table_name == table_name)
            result = await session.execute(stmt)
            version = result.scalar_one_or_none()
            return version
        except Exception as e:
            logger.error(f"Ошибка при получении версии для '{table_name}' из БД: {e}", exc_info=True)
            return None

    @staticmethod
    async def update_db_version(session: AsyncSession, table_name: str, new_hash: str):
        """Обновляет (UPSERT) хэш-версию для таблицы в БД."""
        try:
            stmt = pg_insert(data_versions_table).values(
                table_name=table_name,
                data_hash=new_hash
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=['table_name'],
                set_={'data_hash': new_hash}
            )
            await session.execute(stmt)
            logger.debug(f"Версия для '{table_name}' в БД обновлена на хэш: {new_hash[:8]}...")
        except Exception as e:
            logger.error(f"Ошибка при обновлении версии для '{table_name}' в БД: {e}", exc_info=True)
            raise
        
    @staticmethod
    async def get_redis_version(redis_client: CentralRedisClient, data_key: str) -> Optional[str]:
        """Получает текущую версию данных из Redis по ключу-суффиксу :version."""
        # ВРЕМЕННЫЙ ДЕБАГ-ЛОГ:
        logger.debug(f"DEBUG: DataVersionManager.get_redis_version вызван. redis_client type: {type(redis_client).__name__}, is None: {redis_client is None}")
        if redis_client is None:
            logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: DataVersionManager получил redis_client=None. Это должно быть исправлено.")
            raise ValueError("redis_client в DataVersionManager не может быть None.") # Выбрасываем ошибку явно

        version_key = f"{data_key}:version"
        return await redis_client.get(version_key)   

    @staticmethod
    async def update_redis_version(redis_client: CentralRedisClient, data_key: str, version: str):
        """Обновляет версию данных в Redis."""
        version_key = f"{data_key}:version"
        await redis_client.set(version_key, version)
        logger.debug(f"Версия для ключа '{version_key}' в Redis обновлена на: {version[:8]}...")
        
    @staticmethod
    async def get_redis_fingerprint(redis_client: CentralRedisClient, data_keys: List[str]) -> Dict[str, Optional[str]]:
        """Собирает 'слепок версий' для нескольких ключей данных из Redis."""
        versions = {}
        for key in data_keys:
            versions[key] = await DataVersionManager.get_redis_version(redis_client, key)
        return versions