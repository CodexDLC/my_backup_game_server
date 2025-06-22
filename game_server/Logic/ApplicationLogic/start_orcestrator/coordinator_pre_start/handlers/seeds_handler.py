from .base_step_handler import IPreStartStepHandler
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.load_seeds.seeds_manager import SeedsManager
from game_server.database.models import models

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager


class SeedsHandler(IPreStartStepHandler):
    """ Шаг 1: Загрузка метаданных (Seeds). """
    async def execute(self) -> bool:
        self.logger.debug("⚙️ Шаг 1: Запуск скрипта загрузки метаданных (Seeds)...")
        try:
            # ИЗМЕНЕНО: Получаем RepositoryManager из зависимостей
            repository_manager: RepositoryManager = self.dependencies['repository_manager']
            
            # ИЗМЕНЕНО: Инициализация SeedsManager с RepositoryManager
            seeds_manager = SeedsManager(repository_manager=repository_manager) # Предполагаем, что SeedsManager принимает RepositoryManager
            
            await seeds_manager.import_seeds(models) # models остаются, так как они, вероятно, используются SeedsManager
            self.logger.debug("✅ Шаг 1: Загрузка метаданных завершена успешно.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Шаг 1: Ошибка при загрузке метаданных: {e}", exc_info=True)
            return False