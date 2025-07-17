# game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/handlers/template_planners_handler.py

import logging
import inject
from typing import List, Dict

from .base_step_handler import IPreStartStepHandler
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService
# 👇 ИЗМЕНЕНИЕ: Импортируем только нужные ПЛАНЕРЫ
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.item_generator.item_template_planner import ItemTemplatePlanner
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.template_generator_character.character_template_planner import CharacterTemplatePlanner
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.handler_utils.creature_type_data_orchestrator import CreatureTypeDataOrchestrator
from game_server.config.provider import config


class TemplatePlannersHandler(IPreStartStepHandler):
    """Шаг 2: Запускает высокоуровневые планеры."""

    # 👇 Внедряем только планеры и сервисы
    @inject.autoparams(
        'item_planner',
        'character_planner',
        'creature_orchestrator',
        'arq_service'
    )
    def __init__(self,
                 item_planner: ItemTemplatePlanner, # <-- Получаем наш главный планер предметов
                 character_planner: CharacterTemplatePlanner,
                 creature_orchestrator: CreatureTypeDataOrchestrator,
                 arq_service: ArqQueueService
                 ):
        self.logger = inject.instance(logging.Logger)
        self._item_planner = item_planner
        self._character_planner = character_planner
        self._creature_orchestrator = creature_orchestrator
        self._arq_service = arq_service

    async def execute(self) -> bool:
        self.logger.info("--- ⚙️ Шаг 2: Запуск планировщиков шаблонов ---")
        try:
            # --- Планирование Предметов ---
            item_tasks = await self._item_planner.run_item_planning()
            await self._enqueue_tasks(item_tasks, config.constants.arq.ARQ_TASK_PROCESS_ITEM_GENERATION_BATCH, "предметов")

            # --- Планирование Персонажей ---
            self.logger.info("➡️ Запуск планировщика для шаблонов ПЕРСОНАЖЕЙ...")
            # 👇 ЭТИ ДВЕ СТРОКИ НУЖНО ЗАМЕНИТЬ
            # await self._creature_orchestrator.load_raw_data()
            # await self._creature_orchestrator.process_data_for_generators()
            await self._creature_orchestrator.prepare_data()
            playable_races = self._creature_orchestrator.get_playable_race_list()
            character_tasks = await self._character_planner.pre_process(
                playable_races_data=playable_races,
                desired_gender_ratio=config.settings.prestart.DEFAULT_CHARACTER_GENDER_RATIO
            )
            await self._enqueue_tasks(character_tasks, config.constants.arq.ARQ_TASK_GENERATE_CHARACTER_BATCH, "персонажей")

            self.logger.info("--- ✅ Шаг 2: Планирование шаблонов завершено ---")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Шаг 2: Критическая ошибка при планировании шаблонов: {e}", exc_info=True)
            return False

    # <--- ИЗМЕНЕНИЕ: Метод _enqueue_tasks теперь тоже использует сервис
    async def _enqueue_tasks(self, tasks: List[Dict], task_name: str, entity_name: str):
        if not tasks:
            self.logger.info(f"Планировщик для '{entity_name}' не нашел задач для генерации.")
            return
        
        success_count = 0
        self.logger.info(f"Подготовлено {len(tasks)} батчей задач для '{entity_name}'. Постановка в очередь ARQ...")
        for task_entry in tasks:
            batch_id = task_entry.get("batch_id")
            if batch_id:
                try:
                    # Вызываем метод нашего централизованного сервиса
                    await self._arq_service.enqueue_job(task_name, batch_id=batch_id)
                    success_count += 1
                except Exception:
                    # Логирование ошибки уже происходит внутри сервиса
                    pass # Ошибки уже залогированы в ArqQueueService
            else:
                self.logger.error(f"❌ Пропуск задачи: отсутствует batch_id в {task_entry}.")
        
        # Убираем подсчет ошибок, так как он теперь внутри сервиса
        self.logger.info(f"Итог для '{entity_name}': успешно поставлено {success_count} задач.")