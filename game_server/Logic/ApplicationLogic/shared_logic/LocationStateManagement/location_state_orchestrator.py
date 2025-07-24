# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/location_state_orchestrator.py

import inject
import logging
from typing import Dict, Any, Optional

from game_server.config.constants.arq import ARQ_TASK_AGGREGATE_LOCATION_STATE
from game_server.contracts.dtos.game_commands.data_models import LocationDynamicSummaryDTO
from .Handlers.add_player_to_state_handler import AddPlayerToStateHandler
from .Handlers.remove_player_from_state_handler import RemovePlayerFromStateHandler
from .Handlers.get_location_summary_handler import GetLocationSummaryHandler

# Импортируем сервис для работы с очередью arq
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService


class LocationStateOrchestrator:
    """
    Оркестратор для управления динамическим состоянием локаций (на бэкенде).
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        add_player_handler: AddPlayerToStateHandler,
        remove_player_handler: RemovePlayerFromStateHandler,
        get_summary_handler: GetLocationSummaryHandler,
        arq_service: ArqQueueService,  # <-- НОВАЯ ЗАВИСИМОСТЬ
    ):
        self.logger = logger
        self._add_player_handler = add_player_handler
        self._remove_player_handler = remove_player_handler
        self._get_summary_handler = get_summary_handler
        self._arq_service = arq_service  # <-- СОХРАНЯЕМ СЕРВИС
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def _enqueue_location_update_task(self, location_id: str):
            """
            Ставит задачу в очередь arq для фонового обновления
            центрального кэша Redis и уведомления клиентов.
            """
            if not location_id:
                return
                
            # ✅ ИСПОЛЬЗУЕМ КОНСТАНТУ ВМЕСТО СТРОКИ
            task_name = ARQ_TASK_AGGREGATE_LOCATION_STATE 
            
            self.logger.info(f"Планирование фоновой задачи '{task_name}' для локации {location_id}.")
            try:
                await self._arq_service.enqueue_job(
                    task_name,
                    location_id  # Передаем ID локации как аргумент в таск
                )
                self.logger.info(f"Задача для локации {location_id} успешно поставлена в очередь.")
            except Exception as e:
                self.logger.critical(f"Критическая ошибка при постановке задачи для локации {location_id}: {e}", exc_info=True)

    async def update_player_location_state_and_get_summary(
        self,
        old_location_id: Optional[str],
        new_location_id: str,
        character_id: int
    ) -> LocationDynamicSummaryDTO:
        """
        Обновляет состояние игрока в локациях, возвращает сводку о новой локации
        и ставит фоновые задачи на обновление кэша и рассылку.
        """
        self.logger.debug(f"Обновление состояния игрока {character_id}: из {old_location_id} в {new_location_id}.")

        # 1. Удаляем игрока из старой локации
        if old_location_id:
            await self._remove_player_handler.process(location_id=old_location_id, character_id=character_id)
            self.logger.debug(f"Персонаж {character_id} удален из старой локации {old_location_id}.")
        
        # 2. Добавляем игрока в новую локацию
        summary = await self._add_player_handler.process(location_id=new_location_id, character_id=character_id)
        self.logger.debug(f"Персонаж {character_id} добавлен в новую локацию {new_location_id}. Summary: {summary}.")

        # 3. 🔥 Ставим фоновые задачи в очередь ПОСЛЕ основных операций
        await self._enqueue_location_update_task(old_location_id)
        await self._enqueue_location_update_task(new_location_id)

        return summary

    async def get_location_summary(self, location_id: str) -> LocationDynamicSummaryDTO:
        """
        Получает сводные данные о динамическом состоянии указанной локации.
        """
        self.logger.debug(f"Запрос сводных данных для локации {location_id} через оркестратор.")
        summary = await self._get_summary_handler.process(location_id=location_id)
        return summary