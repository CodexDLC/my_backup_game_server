# game_server/app_discord_bot/app/services/game_world/game_world_data_loader_service.py
# Version: 0.003 # Incrementing version

import inject
import json
from typing import Dict, Any, Optional
from pydantic import ValidationError # 🔥 НОВОЕ: Импортируем ValidationError

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.contracts.dtos.game_world.commands import GetWorldDataCommandDTO
from game_server.contracts.dtos.game_world.data_models import WorldLocationDataDTO
from game_server.contracts.dtos.game_world.results import GetWorldDataResponseData
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload

class GameWorldDataLoaderService:
    """
    Сервис для загрузки статических данных игрового мира (скелета) в Redis.
    Отвечает за прием данных мира (теперь через WebSocket) и их сохранение в глобальном хеше Redis.
    """
    @inject.autoparams()
    def __init__(
        self, 
        game_world_data_manager: IGameWorldDataManager,
        ws_manager: WebSocketManager
    ):
        self._game_world_data_manager = game_world_data_manager
        self._ws_manager = ws_manager
        logger.info("GameWorldDataLoaderService инициализирован.")

    async def load_world_data_from_backend(self) -> None:
        """
        Запрашивает полный скелет игрового мира с бэкенда через WebSocket
        и загружает его в Redis.
        """
        logger.info("Запрос скелета игрового мира с бэкенда через WebSocket...")

        command_dto = GetWorldDataCommandDTO()
        
        try:
            full_message_dict, _ = await self._ws_manager.send_command(
                command_type=command_dto.command,
                command_payload=command_dto.model_dump(),
                domain="system",
                discord_context={}
            )
            logger.info(f"Получен ответ от сервера на команду '{command_dto.command}': {full_message_dict}")

            response_payload_dict = full_message_dict.get('payload', {})
            ws_response_payload = WebSocketResponsePayload(**response_payload_dict)

            if ws_response_payload.status == ResponseStatus.SUCCESS:
                world_data_response = GetWorldDataResponseData(**ws_response_payload.data)
                await self._save_locations_to_redis(world_data_response.locations)
                logger.info("Скелет игрового мира успешно загружен в Redis.")
            else:
                error_message = ws_response_payload.message or "Неизвестная ошибка при запросе данных мира."
                logger.error(f"Ошибка при запросе данных мира с бэкенда: {error_message}")

        except Exception as e:
            logger.error(f"Критическая ошибка при запросе или загрузке скелета игрового мира: {e}", exc_info=True)

    async def _save_locations_to_redis(self, locations_data: Dict[str, WorldLocationDataDTO]) -> None:
        """
        Внутренний метод для сохранения данных локаций в Redis.
        Предварительно очищает существующий хеш и затем заполняет его.
        """
        logger.info("Начало сохранения данных локаций в Redis...")
        
        await self._game_world_data_manager.delete_hash(RedisKeys.GLOBAL_GAME_WORLD_DATA)
        logger.info(f"Существующий хеш Redis '{RedisKeys.GLOBAL_GAME_WORLD_DATA}' очищен.")

        if not locations_data:
            logger.warning("Отсутствуют данные локаций для сохранения.")
            return

        for location_id, location_info_dto in locations_data.items():
            # model_dump() преобразует DTO в словарь, готовый для JSON сериализации
            json_location_data = json.dumps(location_info_dto.model_dump(), ensure_ascii=False)
            
            await self._game_world_data_manager.set_hash_field(
                key=RedisKeys.GLOBAL_GAME_WORLD_DATA,
                field=location_id,
                value=json_location_data
            )
            logger.debug(f"Локация '{location_id}' сохранена в Redis.")
        logger.info("Данные локаций успешно сохранены в Redis.")


    async def get_location_data(self, location_id: str) -> Optional[WorldLocationDataDTO]: # 🔥 ИЗМЕНЕНИЕ: Возвращаемый тип
        """
        Извлекает данные одной локации из статического скелета мира из Redis и валидирует их.
        """
        try:
            json_data = await self._game_world_data_manager.get_hash_field(
                key=RedisKeys.GLOBAL_GAME_WORLD_DATA,
                field=location_id
            )
            if json_data:
                # 🔥 ИЗМЕНЕНИЕ: Валидируем данные в WorldLocationDataDTO
                return WorldLocationDataDTO(**json.loads(json_data))
            return None
        except ValidationError as e:
            logger.error(f"Ошибка валидации Pydantic для данных локации '{location_id}' из Redis: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных локации '{location_id}' из скелета мира: {e}", exc_info=True)
            return None

    async def get_all_locations(self) -> Dict[str, WorldLocationDataDTO]: # 🔥 ИЗМЕНЕНИЕ: Возвращаемый тип
        """
        Извлекает все данные локаций из статического скелета мира из Redis и валидирует их.
        """
        try:
            all_fields = await self._game_world_data_manager.get_all_hash_fields(
                key=RedisKeys.GLOBAL_GAME_WORLD_DATA
            )
            parsed_data = {}
            for field, json_data in all_fields.items():
                try:
                    # 🔥 ИЗМЕНЕНИЕ: Валидируем каждую локацию в WorldLocationDataDTO
                    parsed_data[field] = WorldLocationDataDTO(**json.loads(json_data))
                except ValidationError as e:
                    logger.error(f"Ошибка валидации Pydantic для локации '{field}' из Redis: {e}", exc_info=True)
                    # Можно пропустить некорректные данные или поднять ошибку
                    continue 
                except Exception as e:
                    logger.error(f"Ошибка при парсинге/валидации JSON для локации '{field}' из Redis: {e}", exc_info=True)
                    continue
            return parsed_data
        except Exception as e:
            logger.error(f"Ошибка при получении всех локаций из скелета мира: {e}", exc_info=True)
            return {}
