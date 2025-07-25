# game_server/Logic/InfrastructureLogic/app_cache/services/location/dinamic_location_manager.py

import logging
import inject
from typing import Dict, Any, Optional

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_dinamic_location_manager import IDynamicLocationManager
from game_server.config.constants.redis_key.location_dinamic import LOCATION_SUMMARY_HASH



class DynamicLocationManager(IDynamicLocationManager):
    """
    Сервис для управления кэшем динамических сводных данных о локациях в Redis.
    Отвечает за операции чтения и записи в Redis.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        redis_client: CentralRedisClient
    ):
        self._logger = logger
        self._redis = redis_client
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def update_location_summary(self, location_id: str, summary_data: Dict[str, Any]) -> None:
        """
        Обновляет (полностью перезаписывает) хэш с сводными данными для указанной локации.
        """
        try:
            redis_key = LOCATION_SUMMARY_HASH.format(location_id=location_id)
            await self._redis.redis.hset(redis_key, mapping=summary_data)
            self._logger.info(f"Кэш для локации {location_id} (ключ: {redis_key}) успешно обновлен.")
        except Exception as e:
            self._logger.critical(f"Критическая ошибка при обновлении кэша локации {location_id}: {e}", exc_info=True)
            raise

    async def get_location_summary(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает хэш с сводными данными для указанной локации.
        """
        try:
            redis_key = LOCATION_SUMMARY_HASH.format(location_id=location_id)
            summary_data = await self._redis.redis.hgetall(redis_key)
            
            if not summary_data:
                self._logger.warning(f"Кэш для локации {location_id} (ключ: {redis_key}) не найден или пуст.")
                return None
            
            self._logger.info(f"Кэш для локации {location_id} успешно прочитан.")
            return summary_data
        except Exception as e:
            self._logger.error(f"Ошибка при чтении кэша локации {location_id}: {e}", exc_info=True)
            return None