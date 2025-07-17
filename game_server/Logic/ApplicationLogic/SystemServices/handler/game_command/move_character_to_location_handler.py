# game_server/Logic/ApplicationLogic/SystemServices/handler/game_command/move_character_to_location_handler.py

import logging
import inject
from typing import Any, Dict #, Optional # Optional уже импортирован, если нужен
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession # Этот импорт может быть удален, если AsyncSession не используется напрямую в этом файле


# Интерфейсы обработчиков
from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler

# Репозитории (MongoDB)
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.character_cache.interfaces_character_cache_mongo import IMongoCharacterCacheRepository

# Декоратор для MongoDB транзакций/обработки ошибок
from game_server.Logic.InfrastructureLogic.app_mongo.utils.mongo_transactional_decorator import mongo_transactional

# DTOs
from game_server.contracts.dtos.game_commands.navigation_commands import MoveToLocationCommandDTO, MoveToLocationPayloadDTO, MoveToLocationResultDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail # Убедитесь, что импорт есть

# 🔥 ИСПРАВЛЕНО: Правильный импорт КЛАССА LocationStateOrchestrator
from game_server.Logic.ApplicationLogic.shared_logic.LocationStateManagement.location_state_orchestrator import LocationStateOrchestrator


class MoveCharacterToLocationHandler(ISystemServiceHandler):
    """
    Серверный обработчик для команды перемещения персонажа в новую локацию.
    Обновляет данные о локации персонажа в MongoDB.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        mongo_character_cache_repo: IMongoCharacterCacheRepository,
        # 🔥 ИСПРАВЛЕНО: Инжекция экземпляра LocationStateOrchestrator
        location_state_orchestrator: LocationStateOrchestrator
    ):
        self._logger = logger
        self._mongo_character_cache_repo = mongo_character_cache_repo
        self._location_state_orchestrator = location_state_orchestrator # Теперь это инжектированный экземпляр
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @mongo_transactional()
    async def process(self, command_dto: MoveToLocationCommandDTO) -> BaseResultDTO:
        self.logger.debug(f"Получена команда move_character_to_location: {command_dto.model_dump_json()}")

        character_id = None
        try:
            payload: MoveToLocationPayloadDTO = command_dto.payload
            character_id = payload.character_id
            target_location_id = payload.target_location_id

            # 1. Получение текущего документа персонажа из MongoDB
            character_document = await self._mongo_character_cache_repo.get_character_by_id(character_id)
            if not character_document:
                self.logger.warning(f"Персонаж ID {character_id} не найден в MongoDB для перемещения.")
                return MoveToLocationResultDTO(
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=False,
                    message=f"Персонаж с ID {character_id} не найден.",
                    error=ErrorDetail(code="CHARACTER_NOT_FOUND", message="Character not found."),
                    client_id=command_dto.client_id
                )

            old_location_data = character_document.get("location", {"current": {"location_id": None}, "previous": {"location_id": None}})
            old_current_location_id = old_location_data["current"].get("location_id")
            old_current_region_id = old_location_data["current"].get("region_id")

            if old_current_location_id == target_location_id:
                self.logger.info(f"Персонаж {character_id} уже находится в локации {target_location_id}. Действие не требуется.")
                current_summary = await self._location_state_orchestrator.get_location_summary(target_location_id)
                return MoveToLocationResultDTO(
                    correlation_id=command_dto.correlation_id,
                    trace_id=command_dto.trace_id,
                    span_id=command_dto.span_id,
                    success=True,
                    message=f"Персонаж уже находится в локации {target_location_id}.",
                    data={
                        "ambient_footer_data": {
                            "players_in_location": current_summary.players_in_location,
                            "npcs_in_location": current_summary.npcs_in_location,
                            "last_update": current_summary.last_update
                        }
                    },
                    client_id=command_dto.client_id
                )

            location_summary = await self._location_state_orchestrator.update_player_location_state_and_get_summary(
                old_location_id=old_current_location_id,
                new_location_id=target_location_id,
                character_id=character_id
            )

            # 3. Обновление поля 'location' в документе персонажа
            new_location_data = {
                "current": {"location_id": target_location_id, "region_id": old_current_region_id},
                "previous": {"location_id": old_current_location_id, "region_id": old_current_region_id}
            }
            character_document["location"] = new_location_data

            # 4. Сохранение обновленного документа персонажа в MongoDB
            await self._mongo_character_cache_repo.upsert_character(character_document)

            self.logger.info(f"Персонаж ID {character_id} успешно перемещен в локацию {target_location_id} в MongoDB.")

            # 5. Возвращаем успешный результат с данными из оркестратора
            return MoveToLocationResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=True,
                message=f"Персонаж успешно перемещен в локацию {target_location_id}.",
                data={
                    "ambient_footer_data": {
                        "players_in_location": location_summary.players_in_location,
                        "npcs_in_location": location_summary.npcs_in_location,
                        "last_update": location_summary.last_update
                    }
                },
                client_id=command_dto.client_id
            )

        except ValidationError as e:
            self.logger.error(f"Ошибка валидации DTO в MoveCharacterToLocationHandler: {e.errors()}", exc_info=True)
            return MoveToLocationResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message="Ошибка валидации входных данных.",
                error=ErrorDetail(code="VALIDATION_ERROR", message=str(e)),
                client_id=command_dto.client_id
            )
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в MoveCharacterToLocationHandler для персонажа {character_id}: {e}", exc_info=True)
            return MoveToLocationResultDTO(
                correlation_id=command_dto.correlation_id,
                trace_id=command_dto.trace_id,
                span_id=command_dto.span_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {e}",
                error=ErrorDetail(code="SERVER_ERROR", message=str(e)),
                client_id=command_dto.client_id
            )