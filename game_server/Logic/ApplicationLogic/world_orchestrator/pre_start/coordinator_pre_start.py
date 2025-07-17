# game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/coordinator_pre_start.py
import logging
import inject
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

from .handlers.data_loaders_handler import DataLoadersHandler
from .handlers.template_planners_handler import TemplatePlannersHandler
from .handlers.world_generation_handler import WorldGenerationHandler

class PreStartCoordinator:
    """Главный дирижер режима предстарта."""

    @inject.autoparams()
    def __init__(self, logger: logging.Logger, session_factory: Callable[[], AsyncSession]):
        self.logger = logger
        self._session_factory = session_factory
        self.steps = [
            DataLoadersHandler,
            TemplatePlannersHandler,
            WorldGenerationHandler,
        ]
        self.logger.info(f"PreStartCoordinator инициализирован. Количество шагов: {len(self.steps)}.")

    async def run_pre_start_sequence(self) -> bool:
        """
        Последовательно выполняет все шаги предстарта.
        Вся последовательность обернута в единую транзакцию.
        """
        @transactional(self._session_factory)
        async def _run(session: AsyncSession) -> bool: # 'session' здесь - это сессия для всей последовательности
            self.logger.info("--- 🚀 ЗАПУСК ПОСЛЕДОВАТЕЛЬНОСТИ ПРЕДСТАРТА (ТРАНЗАКЦИОННО) ---")
            self.logger.debug("DEBUG: PreStartCoordinator._run - Начинаем итерацию по шагам.") # 🔥 ДОБАВЛЕН ЛОГ

            for step_class in self.steps:
                self.logger.info(f"Выполнение шага: {step_class.__name__}...")
                try:
                    handler_instance = inject.instance(step_class)
                    self.logger.debug(f"DEBUG: PreStartCoordinator._run - Инстанс {step_class.__name__} получен. Вызываем execute().") # 🔥 ДОБАВЛЕН ЛОГ

                    success = await handler_instance.execute()
                    self.logger.debug(f"DEBUG: PreStartCoordinator._run - Шаг '{step_class.__name__}' вернул success={success} (тип: {type(success)}).") # 🔥 ДОБАВЛЕН ЛОГ

                    if not success:
                        self.logger.critical(f"🚨 ОСТАНОВКА ПРЕДСТАРТА: Шаг '{step_class.__name__}' завершился с ошибкой. Откат транзакции.")
                        return False
                except Exception as e:
                    self.logger.critical(f"🚨 Не удалось создать или выполнить шаг '{step_class.__name__}': {e}", exc_info=True)
                    self.logger.debug(f"DEBUG: PreStartCoordinator._run - Поймано исключение для шага '{step_class.__name__}'. Возвращаем False.") # 🔥 ДОБАВЛЕН ЛОГ
                    return False

            self.logger.info("--- ✅ ПОСЛЕДОВАТЕЛЬНОСТЬ ПРЕДСТАРТА УСПЕШНО ЗАВЕРШЕНА (ТРАНЗАКЦИЯ ЗАКОММИЧЕНА) ---")
            self.logger.debug("DEBUG: PreStartCoordinator._run - Все шаги выполнены успешно. Возвращаем True.") # 🔥 ДОБАВЛЕН ЛОГ
            return True

        self.logger.debug("DEBUG: PreStartCoordinator.run_pre_start_sequence - Вызываем внутренний _run.") # 🔥 ДОБАВЛЕН ЛОГ
        final_result = await _run()
        self.logger.debug(f"DEBUG: PreStartCoordinator.run_pre_start_sequence - _run вернул {final_result}. Возвращаем это.") # 🔥 ДОБАВЛЕН ЛОГ
        return final_result
