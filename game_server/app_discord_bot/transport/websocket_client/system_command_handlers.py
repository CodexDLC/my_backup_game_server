# transport/websocket_client/system_command_handlers.py
from game_server.common_contracts.api_models.gateway_api import BotAcknowledgementRequest
from game_server.common_contracts.shared_models.api_contracts import WebSocketSystemCommandToClientPayload
from game_server.config.logging.logging_setup import app_logger as logger

class WSSystemCommandHandlers:
    """
    Диспетчер для обработки системных команд, полученных от сервера.
    """
    def __init__(self, bot):
        self.bot = bot

    async def handle_command(self, command_data: WebSocketSystemCommandToClientPayload):
        """
        Вызывает нужный обработчик и отправляет HTTP ACK после выполнения.
        """
        command_name = command_data.command_name
        handler_name = f"handle_{command_name.lower()}_command"
        handler_method = getattr(self, handler_name, self.handle_unknown_command)
        
        logger.info(f"Получена системная команда '{command_name}'. Вызов '{handler_name}'...")
        
        status = "failed"
        error_details = "Handler not implemented"
        try:
            await handler_method(command_data)
            status = "success"
            error_details = None
        except Exception as e:
            logger.error(f"Ошибка при выполнении системной команды '{command_name}': {e}", exc_info=True)
            error_details = str(e)
            
        ack_payload = BotAcknowledgementRequest(status=status, error_details=error_details)
        
        try:
            await self.bot.http_manager.gateway.acknowledge_command(
                command_id=str(command_data.command_id), 
                data=ack_payload
            )
            logger.info(f"Отправлен ACK для команды '{command_name}' со статусом '{status}'.")
        except Exception as e:
            logger.error(f"Не удалось отправить ACK для команды '{command_name}': {e}", exc_info=True)


    async def handle_unknown_command(self, command_data: WebSocketSystemCommandToClientPayload):
        logger.warning(f"Получена неизвестная системная команда '{command_data.command_name}'.")
        raise NotImplementedError("Unknown system command")

    # Здесь будут конкретные обработчики
    # async def handle_update_config_command(self, command_data: WebSocketSystemCommandToClientPayload):
    #     logger.info(f"Обработка команды на обновление конфига: {command_data.command_data}")
