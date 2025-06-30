# game_server/Logic/ApplicationLogic/auth_service/auth_service.py

import logging
import os
import uuid
from typing import Dict, Any

from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO
from game_server.common_contracts.shared_models.api_contracts import WebSocketMessage, WebSocketResponsePayload, ResponseStatus
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus

# Импорты, специфичные для этого сервиса
import game_server.game_services.command_center.auth_service_command.auth_service_config as config
from .Handlers.i_auth_handler import IAuthHandler
from game_server.Logic.ApplicationLogic.auth_service.utils.account_helpers import generate_auth_token

BOT_GATEWAY_SECRET = os.getenv("GATEWAY_BOT_SECRET")

class AuthOrchestrator:
    """
    Стандартизированный оркестратор для сервиса аутентификации.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        self.dependencies = dependencies
        self.logger = dependencies.get('logger', logging.getLogger(__name__))
        self.message_bus: IMessageBus = dependencies.get('message_bus')

        self.handlers: Dict[str, IAuthHandler] = {
            command_name: info["handler"](dependencies=self.dependencies)
            for command_name, info in config.COMMAND_DTO_MAPPING.items()
        }
        self.logger.info(f"AuthOrchestrator инициализирован с {len(self.handlers)} обработчиками.")

    async def process_command(self, validated_dto: BaseCommandDTO):
        """
        Главный метод-диспетчер. Получает DTO, находит обработчик и запускает его.
        """
        command_type = validated_dto.command
        handler = self.handlers.get(command_type)
        if not handler:
            self.logger.error(f"Обработчик для команды '{command_type}' не найден.")
            return

        result_dto: BaseResultDTO = await handler.process(validated_dto)

        if result_dto:
            await self._publish_response(result_dto)

    async def _publish_response(self, result_dto: BaseResultDTO):
        """
        СТАНДАРТНЫЙ МЕТОД ОТПРАВКИ ОТВЕТА.
        Формирует WebSocketMessage и публикует его в Events.
        """
        client_id_for_delivery = getattr(result_dto, 'client_id', None)
        if not client_id_for_delivery:
            self.logger.warning(f"Результат для CorrID {result_dto.correlation_id} не может быть доставлен: отсутствует client_id.")
            return

        response_payload = WebSocketResponsePayload(
            request_id=result_dto.correlation_id,
            status=ResponseStatus.SUCCESS if result_dto.success else ResponseStatus.FAILURE,
            message=result_dto.message,
            data=result_dto.data,
            error=result_dto.error
        )

        websocket_message = WebSocketMessage(
            type="RESPONSE",
            correlation_id=result_dto.correlation_id,
            trace_id=result_dto.trace_id,
            span_id=result_dto.span_id,
            client_id=client_id_for_delivery,
            payload=response_payload,
        )

        domain = getattr(result_dto, 'domain', 'auth')
        action = getattr(result_dto, 'action', 'default')
        status_str = "success" if result_dto.success else "failure"
        routing_key = f"response.{domain}.{action}.{status_str}"

        await self.message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=websocket_message.model_dump(mode='json')
        )
        self.logger.info(f"Ответ для CorrID {result_dto.correlation_id} опубликован в {Exchanges.EVENTS} с ключом '{routing_key}'.")

    async def validate_session_token(self, rpc_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Метод для RPC-вызова от Gateway для валидации токена.
        Теперь обрабатывает токены, выданные AuthService.
        """
        token = rpc_payload.get("token")
        client_type = rpc_payload.get("client_type")
        # bot_name = rpc_payload.get("bot_name") # bot_name больше не нужен для валидации здесь

        if not token:
            self.logger.warning("RPC-запрос на валидацию токена без токена.")
            return {"is_valid": False, "error": "Token is missing."}

        session_manager = self.dependencies.get('session_manager')
        if not session_manager:
            self.logger.critical("SessionManager не найден в зависимостях AuthService для валидации токена!")
            return {"is_valid": False, "error": "Server internal error: SessionManager missing."}

        # 🔥 ИЗМЕНЕНО: Универсальная валидация токена через session_manager
        # session_manager.get_player_id_from_session теперь универсален для бота и игрока
        client_id = await session_manager.get_player_id_from_session(token)

        if client_id:
            # Определяем фактический тип клиента по сохраненному ID
            if client_id.startswith("BOT_"):
                validated_client_type = "DISCORD_BOT"
                validated_client_id = client_id.replace("BOT_", "") # Получаем имя бота
                self.logger.info(f"✅ Discord Bot '{validated_client_id}' успешно аутентифицирован по токену.")
            else:
                validated_client_type = "PLAYER" # Или другой тип клиента, если у вас их несколько
                validated_client_id = client_id
                self.logger.info(f"✅ Player {validated_client_id} успешно аутентифицирован по токену.")

            return {"is_valid": True, "client_id": validated_client_id, "client_type": validated_client_type}
        else:
            self.logger.warning("❌ Аутентификация клиента не удалась: неверный или истекший токен.")
            return {"is_valid": False, "error": "Invalid or expired token."}


    async def issue_auth_token(self, rpc_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Выдает токен аутентификации для различных типов клиентов (бот, игрок).
        """
        client_type = rpc_payload.get("client_type")
        issued_token = None
        client_id_to_save = None

        if client_type == "DISCORD_BOT":
            bot_name = rpc_payload.get("bot_name")
            bot_secret_from_request = rpc_payload.get("bot_secret")

            if BOT_GATEWAY_SECRET is None:
                self.logger.critical("GATEWAY_BOT_SECRET не установлен в настройках AuthService! Бот не может быть аутентифицирован.")
                return {"success": False, "error": "Server configuration error: BOT_SECRET_NOT_SET."}

            if bot_secret_from_request == BOT_GATEWAY_SECRET and bot_name:
                issued_token = await generate_auth_token()
                client_id_to_save = f"BOT_{bot_name}"
                self.logger.info(f"Учетные данные Discord Bot '{bot_name}' подтверждены.")
            else:
                self.logger.warning(f"Запрос на выдачу токена Discord-боту '{bot_name}' отклонен: неверный секрет.")
                return {"success": False, "error": "Invalid bot secret."}

        elif client_type == "PLAYER":
            username = rpc_payload.get("username")
            password = rpc_payload.get("password")
            
            is_valid_credentials = True # Временная заглушка
            player_id = "some_player_id" # TODO: Получить реальный player_id из БД после валидации учетных данных

            if is_valid_credentials:
                issued_token = await generate_auth_token()
                client_id_to_save = player_id
                self.logger.info(f"Учетные данные игрока '{username}' подтверждены.")
            else:
                self.logger.warning(f"Запрос на выдачу токена игроку '{username}' отклонен: неверные учетные данные.")
                return {"success": False, "error": "Invalid credentials."}
        
        else:
            self.logger.warning(f"Запрос на выдачу токена с неизвестным типом клиента: {client_type}.")
            return {"success": False, "error": "Unknown client type for token issuance."}

        if issued_token:
            session_manager = self.dependencies.get('session_manager')
            if not session_manager:
                self.logger.critical("SessionManager не найден в зависимостях AuthService для выдачи токена!")
                return {"success": False, "error": "Server internal error: SessionManager missing."}

            await session_manager.save_session(client_id=client_id_to_save, token=issued_token)
            
            self.logger.info(f"Токен успешно выдан для клиента '{client_id_to_save}': ...{issued_token[-6:]}")
            return {"success": True, "token": issued_token, "expires_in": 3600}
        else:
            return {"success": False, "error": "Failed to issue token due to unknown reason."}

