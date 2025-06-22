from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.data_processing.creature_type_data_orchestrator import CreatureTypeDataOrchestrator
from .base_step_handler import IPreStartStepHandler


# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

class InitializeDataLoadersHandler(IPreStartStepHandler):
    """ Шаг 3: Инициализация загрузчиков данных для генераторов. """
    async def execute(self) -> bool:
        self.logger.debug("⚙️ Шаг 3: Инициализация загрузчиков данных для генераторов...")
        try:
            # ИЗМЕНЕНО: Получаем RepositoryManager из зависимостей
            repository_manager: RepositoryManager = self.dependencies['repository_manager']
            
            # ИЗМЕНЕНО: Инициализация CreatureTypeDataOrchestrator с RepositoryManager
            # async with async_session_factory() as session: # УДАЛЕНО
            #     orchestrator = CreatureTypeDataOrchestrator(session) # УДАЛЕНО
            orchestrator = CreatureTypeDataOrchestrator(repository_manager=repository_manager) # ИЗМЕНЕНО
            
            await orchestrator.load_raw_data()
            await orchestrator.process_data_for_generators()
                
            # 🔥 ВАЖНО: Сохраняем созданный оркестратор в общий словарь зависимостей
            # чтобы следующий обработчик в конвейере мог его использовать.
            self.dependencies['creature_type_orchestrator'] = orchestrator
                
            self.logger.debug("✅ Шаг 3: Загрузчики данных успешно инициализированы.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Шаг 3: Ошибка при инициализации загрузчиков данных: {e}", exc_info=True)
            return False