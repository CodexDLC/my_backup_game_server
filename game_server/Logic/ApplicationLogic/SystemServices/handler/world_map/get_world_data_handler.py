# game_server/Logic/ApplicationLogic/SystemServices/handler/world_map/get_world_data_handler.py
# Version: 0.002

import logging
from typing import Dict, Any, Optional
import inject # ▼▼▼ НОВЫЙ ИМПОРТ: inject ▼▼▼

from game_server.contracts.dtos.game_world.commands import GetWorldDataCommandDTO
from game_server.contracts.dtos.game_world.data_models import WorldLocationDataDTO
from game_server.contracts.dtos.game_world.results import GetWorldDataResponseData
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import IWorldStateRepository


class GetWorldDataHandler(ISystemServiceHandler):
    """
    Обработчик команды 'get_world_data'.
    Отвечает за извлечение всего статического скелета игрового мира из MongoDB
    и формирование ответа для бота.
    """
    # ▼▼▼ ИСПОЛЬЗУЕМ @inject.autoparams() И ЯВНО ОБЪЯВЛЯЕМ ЗАВИСИМОСТИ ▼▼▼
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, world_state_repo: IWorldStateRepository):
        self._logger = logger
        self.world_state_repo: IWorldStateRepository = world_state_repo
        self._logger.info("GetWorldDataHandler инициализирован.")

    # ▼▼▼ РЕАЛИЗАЦИЯ АБСТРАКТНОГО СВОЙСТВА logger ИЗ ISystemServiceHandler ▼▼▼
    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, command_dto: BaseCommandDTO) -> BaseResultDTO:
        """
        Обрабатывает команду GetWorldDataCommandDTO.
        Извлекает данные мира из репозитория и возвращает их в BaseResultDTO.
        """
        self.logger.info(f"Начало обработки команды 'get_world_data' (CorrID: {command_dto.correlation_id}).")

        if not isinstance(command_dto, GetWorldDataCommandDTO):
            self.logger.error(f"Некорректный DTO для GetWorldDataHandler: {type(command_dto)}. Ожидается GetWorldDataCommandDTO.")
            return BaseResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message="Некорректный формат команды.",
                error={"code": "INVALID_COMMAND_DTO", "message": "Invalid DTO type for handler."},
                client_id=command_dto.client_id
            )

        try:
            # ▼▼▼ ИЗВЛЕЧЕНИЕ ДАННЫХ МИРА ИЗ MONGO DB ▼▼▼
            # Используем get_all_regions() для получения всех документов-регионов.
            # Каждый документ-регион содержит вложенный словарь 'locations'.
            all_region_documents = await self.world_state_repo.get_all_regions() 
            
            combined_locations_data: Dict[str, Dict[str, Any]] = {}

            # Итерируем по каждому документу региона и извлекаем его локации
            for region_doc in all_region_documents:
                locations_in_region = region_doc.get("locations", {})
                combined_locations_data.update(locations_in_region) # Объединяем локации из всех регионов

            if not combined_locations_data:
                self.logger.warning("В MongoDB не найдены данные локаций для загрузки.")
                # Можно вернуть успешный результат с пустыми данными, если это ожидаемое состояние
                return BaseResultDTO(
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=True,
                    message="Статические данные игрового мира получены, но локации отсутствуют.",
                    data=GetWorldDataResponseData(locations={}).model_dump(),
                    client_id=command_dto.client_id
                )

            # Валидируем и преобразуем каждую локацию в WorldLocationDataDTO
            # Это гарантирует, что данные соответствуют DTO, и отфильтровывает лишние поля
            validated_locations: Dict[str, WorldLocationDataDTO] = {
                loc_id: WorldLocationDataDTO(**loc_data)
                for loc_id, loc_data in combined_locations_data.items()
            }

            # Формируем DTO ответа
            response_data_dto = GetWorldDataResponseData(locations=validated_locations)

            self.logger.info(f"Данные мира успешно получены для команды 'get_world_data' (CorrID: {command_dto.correlation_id}).")
            return BaseResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message="Статические данные игрового мира успешно получены.",
                data=response_data_dto.model_dump(), # Преобразуем DTO в словарь для payload
                client_id=command_dto.client_id
            )

        except Exception as e:
            self.logger.exception(f"Ошибка при получении статических данных мира для команды 'get_world_data' (CorrID: {command_dto.correlation_id}).")
            return BaseResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Ошибка сервера при получении данных мира: {e}",
                error={"code": "WORLD_DATA_FETCH_ERROR", "message": str(e)},
                client_id=command_dto.client_id
            )
