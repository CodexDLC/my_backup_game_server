# game_server/app_discord_bot/app/services/game_modules/cache_update/logic_handlers/update_location_cache_handler.py

import json
import logging
import inject
from typing import Dict, Any

from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.contracts.dtos.game_commands.cache_request_commands import GetLocationSummaryCommandDTO, GetLocationSummaryPayloadDTO, GetLocationSummaryResultDTO
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload


class UpdateLocationCacheHandler:
    """
    Обрабатывает команду 'update_location'.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        ws_manager: WebSocketManager,
        game_world_data_manager: IGameWorldDataManager
    ):
        self.logger = logger
        self._ws_manager = ws_manager
        self._cache = game_world_data_manager
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, data: Dict[str, Any]):
        location_id = data.get("location_id")
        if not location_id:
            self.logger.warning("Команда 'update_location' вызвана без 'location_id'.")
            return

        self.logger.info(f"Начинаю обновление кэша для локации {location_id}...")

        try:
            # 1. Формируем DTO для бэкенда
            payload = GetLocationSummaryPayloadDTO(location_id=location_id)
            command_to_backend = GetLocationSummaryCommandDTO(payload=payload)

            # 2. Отправляем команду и ждем ответа
            response_data_raw, _ = await self._ws_manager.send_command(
                command_type=command_to_backend.command,
                command_payload=command_to_backend.model_dump(),
                domain="cache",
                discord_context={} 
            )
            
            # 3. Распаковываем ответ
            response_payload_ws = WebSocketResponsePayload(**response_data_raw.get('payload', {}))
            backend_result = GetLocationSummaryResultDTO(
                correlation_id=response_payload_ws.request_id,
                success=response_payload_ws.status == ResponseStatus.SUCCESS,
                message=response_payload_ws.message,
                data=response_payload_ws.data,
                error=response_payload_ws.error
            )

            # 4. Обрабатываем результат
            if backend_result.success:
                fresh_data = backend_result.data
                if fresh_data:
                    # 5. ✅ ГОТОВИМ ДАННЫЕ: Превращаем списки/словари в JSON-строки
                    prepared_data_for_cache = {
                        key: json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                        for key, value in fresh_data.items()
                    }
                    
                    # 6. Вызываем менеджер с уже подготовленными данными
                    await self._cache.set_dynamic_location_data(location_id, prepared_data_for_cache)
                    self.logger.info(f"Локальный кэш для локации {location_id} успешно обновлен.")
                else:
                    self.logger.warning(f"Бэкенд вернул успех, но нет данных для локации {location_id}.")
            else:
                error_msg = backend_result.message or "Неизвестная ошибка от бэкенда"
                self.logger.error(f"Не удалось обновить данные для локации {location_id}: {error_msg}")

        except Exception as e:
            self.logger.critical(f"Критическая ошибка в UpdateLocationCacheHandler для локации {location_id}: {e}", exc_info=True)
