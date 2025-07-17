# game_server/Logic/ApplicationLogic/auth_service/Handlers/auth_validate_token_rpc_handler.py

import logging
from typing import Dict, Any
import inject

# Импортируем зависимости, которые нужны этому обработчику
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.contracts.dtos.auth.commands import ValidateTokenRpcCommandDTO


class AuthValidateTokenRpcHandler:
    """
    Обработчик для RPC-команды на валидацию токена сессии.
    """
    @inject.autoparams('session_manager') # Убираем 'logger'
    def __init__(
        self,
        session_manager: ISessionManager
    ):
        self.logger = inject.instance(logging.Logger) # Логгер явно получается через inject.instance()
        self.session_manager = session_manager
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(self, rpc_payload_dto: ValidateTokenRpcCommandDTO) -> Dict[str, Any]:
        """
        Выполняет логику валидации токена.
        """
        token = rpc_payload_dto.token
        self.logger.info(f"Запрос на валидацию токена (последние 6 симв): ...{token[-6:]}")

        if not token:
            return {"is_valid": False, "error": "Token is missing.", "error_code": "TOKEN_MISSING"}

        try:
            client_id = await self.session_manager.get_player_id_from_session(token)
        except Exception as e:
            self.logger.error(f"Ошибка при получении client_id из SessionManager: {e}", exc_info=True)
            return {"is_valid": False, "error": f"Internal server error during token lookup: {e}", "error_code": "TOKEN_LOOKUP_ERROR"}

        if client_id:
            if client_id.startswith("BOT_"):
                validated_client_type = "DISCORD_BOT"
                validated_client_id = client_id.replace("BOT_", "")
            else:
                validated_client_type = "PLAYER"
                validated_client_id = client_id
            
            self.logger.info(f"Токен валиден. client_id: {validated_client_id}, client_type: {validated_client_type}")
            return {"is_valid": True, "client_id": validated_client_id, "client_type": validated_client_type, "error": None}
        else:
            self.logger.warning(f"Аутентификация не удалась: неверный или истекший токен ...{token[-6:]}.")
            return {"is_valid": False, "error": "Invalid or expired token.", "error_code": "INVALID_EXPIRED_TOKEN"}