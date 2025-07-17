# game_server/Logic/InfrastructureLogic/app_cache/services/session/session_manager.py

import logging

import inject
from game_server.config.logging.logging_setup import app_logger as logger
from typing import Optional

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
# 🔥 ИЗМЕНЕНИЕ: Импортируем константы из нового, специального файла
from game_server.config.constants.redis_key.session_keys import KEY_SESSION, SESSION_TTL_SECONDS


class RedisSessionManager(ISessionManager):
    """
    Реализация менеджера сессий, использующая Redis в качестве хранилища.
    """
    @inject.autoparams()
    def __init__(self, redis_client: CentralRedisClient, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger
        self.logger.info(f"✨ {self.__class__.__name__} (v2) инициализирован.")

    async def save_session(self, client_id: str, token: str) -> None:
        """
        Сохраняет сессию в Redis, используя предоставленный токен и ID клиента.
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон для формирования ключа
        session_key = KEY_SESSION.format(token=token)
        await self.redis_client.set(
            key=session_key,
            value=client_id,
            ex=SESSION_TTL_SECONDS
        )
        logger.debug(f"Сессия для client_id '{client_id}' сохранена с токеном: ...{token[-6:]}")


    async def get_player_id_from_session(self, token: str) -> Optional[str]:
        """
        Извлекает ID клиента (игрока или бота) из Redis по токену сессии.
        """
        if not token:
            return None

        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон для формирования ключа
        session_key = KEY_SESSION.format(token=token)
        client_id_from_redis = await self.redis_client.get(key=session_key)

        if client_id_from_redis:
            logger.debug(f"Токен ...{token[-6:]} успешно валидирован для client_id '{client_id_from_redis}'.")
        else:
            logger.debug(f"Токен ...{token[-6:]} не найден или истек.")

        return client_id_from_redis

    async def delete_player_session(self, token: str) -> None:
        """
        Удаляет сессию из Redis.
        """
        if not token:
            return

        # 🔥 ИЗМЕНЕНИЕ: Используем новый шаблон для формирования ключа
        session_key = KEY_SESSION.format(token=token)
        deleted_count = await self.redis_client.delete(session_key)
        if deleted_count > 0:
            logger.debug(f"Сессия с токеном ...{token[-6:]} была удалена.")