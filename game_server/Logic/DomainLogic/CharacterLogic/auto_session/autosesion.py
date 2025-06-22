from datetime import datetime, timedelta
from typing import Literal, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging # Добавляем для логирования

from game_server.Logic.DomainLogic.dom_utils.account_identifiers import AccountIdentifiers
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.manager_tick_handler.ORM_Auto_Sessions import AutoSessionsManager

ActionType = Literal["start", "stop", "status", "update"]
IdentifierType = Literal["id", "name", "discord_id"]

logger = logging.getLogger(__name__) # Инициализация логгера

class AutoSession:
    """Лёгкая обёртка над AutoSessionsManager."""
    
    def __init__(self, db_session: AsyncSession):
        self.manager = AutoSessionsManager(db_session)
        self.identifiers = AccountIdentifiers(db_session)
        logger.info("AutoSession (логика) инициализирована.") # Логирование инициализации

    async def handle(
        self,
        request_data: Dict[str, Any] # <--- Теперь принимает один словарь
    ) -> Dict[str, Any]:
        """
        Обрабатывает запросы на управление авто-сессиями.
        Принимает словарь с ключами 'action', 'identifier_type', 'identifier_value', 'category'.
        """
        action = request_data.get("action")
        identifier_type = request_data.get("identifier_type")
        identifier_value = request_data.get("identifier_value")
        category = request_data.get("category")

        # Добавляем валидацию входящих данных здесь, так как роут передает уже не Pydantic-модель
        if not all([action, identifier_type, identifier_value]):
            logger.warning(f"Недостающие обязательные поля в запросе AutoSession: {request_data}")
            raise ValueError("Недостающие обязательные поля: 'action', 'identifier_type', 'identifier_value'.")
        
        # Проверяем, что action имеет ожидаемый тип (если нужно)
        if action not in ["start", "stop", "status", "update"]:
            logger.warning(f"Неверное значение 'action': {action}")
            raise ValueError("Неверное значение для 'action'.")

        logger.info(f"Обработка AutoSession: action='{action}', identifier='{identifier_type}:{identifier_value}'.")

        if not (character_id := await self.identifiers.get_character_id(identifier_type, identifier_value)):
            logger.warning(f"Персонаж не найден для identifier_type='{identifier_type}', identifier_value='{identifier_value}'.")
            return {"status": "error", "message": "Персонаж не найден!"}

        try:
            match action:
                case "start":
                    if not category:
                        logger.warning(f"Для действия 'start' отсутствует 'category'.")
                        raise ValueError("Для действия 'start' обязателен 'category'.")
                    return await self._start(character_id, category)
                case "stop":
                    return await self.manager.delete_session(character_id)
                case "status":
                    return await self.manager.get_session(character_id)
                case "update":
                    return await self._update(character_id)
                case _: # Это уже не должно достигаться благодаря проверке выше
                    logger.error(f"Неизвестное действие: {action} после внутренней валидации.")
                    return {"status": "error", "message": "Неверная команда!"}
        except ValueError as e: # Ловим ValueError из внутренних проверок
            logger.warning(f"Ошибка логики AutoSession: {e}")
            raise # Пробрасываем для обработки в роуте
        except Exception as e:
            logger.error(f"Непредвиденная ошибка в AutoSession.handle: {e}", exc_info=True)
            return {"status": "error", "message": f"Ошибка: {e}"}

    async def _start(self, character_id: int, category: str) -> Dict[str, Any]:
        """Сокращённый вызов менеджера для старта сессии."""
        logger.debug(f"Старт сессии для персонажа {character_id} в категории '{category}'.")
        return await self.manager.create_session(
            character_id=character_id,
            active_category=category,
            next_tick_at=datetime.utcnow() + timedelta(minutes=6),
            last_tick_at=datetime.utcnow()
        )

    async def _update(self, character_id: int) -> Dict[str, Any]:
        """Сокращённый вызов для обновления."""
        logger.debug(f"Обновление сессии для персонажа {character_id}.")
        return await self.manager.update_session(
            character_id,
            {"next_tick_at": datetime.utcnow() + timedelta(minutes=6)}
        )