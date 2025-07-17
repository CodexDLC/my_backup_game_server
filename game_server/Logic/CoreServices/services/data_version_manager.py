# game_server/Logic/CoreServices/services/data_version_manager.py

from datetime import datetime
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional, Callable
from uuid import UUID
import msgpack
import inject

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import Column, String, Table, MetaData

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# 🔥 ДОБАВЛЕНО: Импорт для фабрики репозитория версий данных
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository


# --- Определение таблицы для хранения версий (без изменений) ---
metadata_obj = MetaData()

data_versions_table = Table(
    'data_versions',
    metadata_obj,
    Column('table_name', String, primary_key=True, comment="Имя таблицы или логической группы данных"),
    Column('data_hash', String, nullable=False, comment="Хэш-сумма данных данных (SHA256)")
)

def _custom_json_serializer_for_hash(obj):
    """
    Кастомный сериализатор для JSON, используемый только при вычислении хэша.
    Умеет обрабатывать UUID и datetime объекты.
    """
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class DataVersionManager:
    """
    Универсальный сервис для управления версиями справочных данных
    в PostgreSQL и кэширования их в Redis.
    """
    @inject.autoparams()
    def __init__(
        self,
        redis_client: CentralRedisClient, # Теперь redis_client инжектируется
        session_factory: Callable[[], AsyncSession], # Фабрика сессий для методов, работающих с БД
        # 🔥 ИЗМЕНЕНО: Сделаем тип более специфичным: Any -> IDataVersionRepository
        data_version_repo_factory: Callable[[AsyncSession], IDataVersionRepository],
        logger: logging.Logger
    ):
        self.redis_client = redis_client
        self._session_factory = session_factory
        self._data_version_repo_factory = data_version_repo_factory
        self.logger = logger
        self.logger.info("✅ DataVersionManager инициализирован как сервис.")

    @staticmethod
    def _calculate_data_hash(data_list: List[Dict[str, Any]]) -> str:
        """
        Вычисляет SHA256 хэш для списка словарей, представляющих данные.
        """
        if not data_list:
            return hashlib.sha256(b"").hexdigest()

        try:
            serialized_items = []
            for item in data_list:
                serialized_item = json.dumps(item, sort_keys=True, default=_custom_json_serializer_for_hash)
                serialized_items.append(serialized_item)

            serialized_items.sort()
            combined_string = "".join(serialized_items)

            logging.getLogger(__name__).debug(f"DEBUG_HASH_STRING (first 500 chars): {combined_string[:500]}")

            return hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
        except TypeError as e:
            logging.getLogger(__name__).error(f"Ошибка сериализации данных для хэширования: {e}", exc_info=True)
            raise
        except Exception as e:
            logging.getLogger(__name__).critical(f"Критическая ошибка при вычислении хэша данных: {e}", exc_info=True)
            raise

    async def get_db_version(self, table_name: str) -> Optional[str]:
        async with self._session_factory() as session:
            try:
                data_version_repo = self._data_version_repo_factory(session)
                version = await data_version_repo.get_current_data_version(table_name)
                return version
            except Exception as e:
                self.logger.error(f"Ошибка при получении версии для '{table_name}' из БД: {e}", exc_info=True)
                return None

    async def update_db_version(self, table_name: str, new_hash: str):
        async with self._session_factory() as session:
            try:
                data_version_repo = self._data_version_repo_factory(session)
                await data_version_repo.update_version(table_name, new_hash)
                self.logger.debug(f"Версия для '{table_name}' в БД обновлена на хэш: {new_hash[:8]}...")
                await session.commit()
            except Exception as e:
                self.logger.error(f"Ошибка при обновлении версии для '{table_name}' в БД: {e}", exc_info=True)
                raise
            
    async def get_redis_version(self, data_key: str) -> Optional[str]:
        """
        Получает текущую хэш-версию для данных из Redis по ключу-суффиксу :version.
        """
        self.logger.debug(f"DEBUG: DataVersionManager.get_redis_version вызван. redis_client type: {type(self.redis_client).__name__}")
        if self.redis_client is None:
            self.logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: DataVersionManager получил redis_client=None. Это должно быть исправлено.")
            raise ValueError("redis_client в DataVersionManager не может быть None.")

        version_key = f"{data_key}:version"
        version_data = await self.redis_client.get_msgpack(version_key)
        if version_data is None:
            return None
        if not isinstance(version_data, str):
            self.logger.error(f"Полученный из Redis хэш версии для '{data_key}' не является строкой. Тип: {type(version_data).__name__}. Значение: {version_data}")
            return None
        return version_data

    async def update_redis_version(self, data_key: str, version: str):
        """
        Обновляет версию данных в Redis.
        """
        version_key = f"{data_key}:version"
        packed_version = msgpack.packb(version, use_bin_type=True)
        set_success = await self.redis_client.set_msgpack(version_key, packed_version)
        if not set_success:
            self.logger.error(f"Не удалось записать версию для ключа '{version_key}' в Redis. Результат set_success: {set_success}")
            raise RuntimeError(f"Не удалось обновить версию Redis для '{data_key}'.")
        
        self.logger.debug(f"Версия для ключа '{version_key}' в Redis обновлена на: {version[:8]}...")
        
    async def get_redis_fingerprint(self, data_keys: List[str]) -> Dict[str, Optional[str]]:
        """Собирает 'слепок версий' для нескольких ключей данных из Redis."""
        versions = {}
        for key in data_keys:
            versions[key] = await self.get_redis_version(key) # Вызываем метод экземпляра
        return versions
