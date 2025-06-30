# game_server/Logic/CoreServices/services/data_version_manager.py

from datetime import datetime # Добавлен импорт datetime, так как он используется в _json_serializer_with_uuid
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import msgpack # Для работы с MsgPack

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import Column, String, Table, MetaData

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.logging.logging_setup import app_logger as logger

# --- Определение таблицы для хранения версий (без изменений) ---
metadata_obj = MetaData()

data_versions_table = Table(
    'data_versions',
    metadata_obj,
    Column('table_name', String, primary_key=True, comment="Имя таблицы или логической группы данных"),
    Column('data_hash', String, nullable=False, comment="Хэш-сумма данных (SHA256)")
)

# 🔥 ИЗМЕНЕНИЕ: Функцию _json_serializer_with_uuid переименовываем
# так как она используется только для json.dumps в _calculate_data_hash
# и ее название должно отражать ее реальное использование
def _custom_json_serializer_for_hash(obj):
    """
    Кастомный сериализатор для JSON, используемый только при вычислении хэша.
    Умеет обрабатывать UUID и datetime объекты.
    """
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime): # Используем datetime из import datetime
        return obj.isoformat()
    # Если obj является объектом, который не может быть сериализован по умолчанию,
    # raise TypeError, как и раньше.
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
        Использует JSON-сериализацию с сортировкой ключей для детерминированного хэша.
        """
        if not data_list:
            return hashlib.sha256(b"").hexdigest()

        try:
            serialized_items = []
            for item in data_list:
                # Гарантируем сортировку ключей словаря для детерминированного JSON
                # 🔥 ИЗМЕНЕНИЕ: Используем переименованный сериализатор
                serialized_item = json.dumps(item, sort_keys=True, default=_custom_json_serializer_for_hash)
                serialized_items.append(serialized_item)

            # Сортируем список JSON-строк для детерминированного порядка всего списка
            serialized_items.sort()

            # Объединяем все отсортированные JSON-строки в одну большую строку
            combined_string = "".join(serialized_items)

            logger.debug(f"DEBUG_HASH_STRING (first 500 chars): {combined_string[:500]}")

            return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        except TypeError as e:
            logger.error(f"Ошибка сериализации данных для хэширования: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.critical(f"Критическая ошибка при вычислении хэша данных: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_db_version(session: AsyncSession, table_name: str) -> Optional[str]:
        # Этот метод работает с БД, не с Redis, поэтому он не меняется
        try:
            stmt = fselect(data_versions_table.c.data_hash).where(data_versions_table.c.table_name == table_name)
            result = await session.execute(stmt)
            version = result.scalar_one_or_none()
            return version
        except Exception as e:
            logger.error(f"Ошибка при получении версии для '{table_name}' из БД: {e}", exc_info=True)
            return None

    @staticmethod
    async def update_db_version(session: AsyncSession, table_name: str, new_hash: str):
        # Этот метод работает с БД, не с Redis, поэтому он не меняется
        try:
            insert_stmt = pg_insert(data_versions_table).values(
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
        """
        Получает текущую хэш-версию для данных из Redis по ключу-суффиксу :version.
        Теперь использует get_msgpack для чтения, так как версии теперь хранятся как MsgPack.
        """
        logger.debug(f"DEBUG: DataVersionManager.get_redis_version вызван. redis_client type: {type(redis_client).__name__}")
        if redis_client is None:
            logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: DataVersionManager получил redis_client=None. Это должно быть исправлено.")
            raise ValueError("redis_client в DataVersionManager не может быть None.")

        version_key = f"{data_key}:version"
        version_data = await redis_client.get_msgpack(version_key)
        if version_data is None:
            return None
        if not isinstance(version_data, str):
            logger.error(f"Полученный из Redis хэш версии для '{data_key}' не является строкой. Тип: {type(version_data).__name__}. Значение: {version_data}")
            return None
        return version_data

    @staticmethod
    async def update_redis_version(redis_client: CentralRedisClient, data_key: str, version: str):
        """
        Обновляет версию данных в Redis.
        Теперь использует set_msgpack для записи, так как версии теперь хранятся как MsgPack.
        """
        version_key = f"{data_key}:version"
        packed_version = msgpack.packb(version, use_bin_type=True)
        set_success = await redis_client.set_msgpack(version_key, packed_version)
        if not set_success:
            logger.error(f"Не удалось записать версию для ключа '{version_key}' в Redis. Результат set_msgpack: {set_success}")
            raise RuntimeError(f"Не удалось обновить версию Redis для '{data_key}'.")
        
        logger.debug(f"Версия для ключа '{version_key}' в Redis обновлена на: {version[:8]}...")
        
    @staticmethod
    async def get_redis_fingerprint(redis_client: CentralRedisClient, data_keys: List[str]) -> Dict[str, Optional[str]]:
        """Собирает 'слепок версий' для нескольких ключей данных из Redis."""
        versions = {}
        for key in data_keys:
            versions[key] = await DataVersionManager.get_redis_version(redis_client, key)
        return versions