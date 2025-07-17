# game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/handlers/data_loaders_handler.py

import logging
import inject
from typing import Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты для DataLoadersHandler
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.seeds_manager import SeedsManager
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.reference_data_loader import ReferenceDataLoader

# 🔥 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Импортируем именно модуль, содержащий ВСЕ ORM-модели
from game_server.database.models import models as orm_models # Теперь orm_models ссылается на game_server.database.models.models

class DataLoadersHandler:
    """
    Обработчик для шага загрузки данных в PreStartCoordinator.
    Отвечает за запуск SeedsManager и ReferenceDataLoader.
    Является транзакционной границей.
    """
    @inject.autoparams()
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession], # Фабрика сессий
        seeds_manager: SeedsManager, # Инжектируем SeedsManager
        reference_data_loader: ReferenceDataLoader, # Инжектируем ReferenceDataLoader
        logger: logging.Logger
    ):
        self._session_factory = session_factory
        self._seeds_manager = seeds_manager
        self._reference_data_loader = reference_data_loader
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self) -> bool: # 🔥 ИЗМЕНЕНО: Явно указываем, что метод возвращает bool
        self.logger.info("➡️ Выполнение шага: DataLoadersHandler...")
        self.logger.debug("DEBUG: DataLoadersHandler.execute - Начинаем выполнение.")
        
        try:
            async with self._session_factory() as session: # Открываем сессию для всей операции
                self.logger.debug("DEBUG: DataLoadersHandler.execute - Сессия открыта. Запускаем SeedsManager.import_seeds.")
                seeds_import_success = await self._seeds_manager.import_seeds(session, orm_models)
                self.logger.debug(f"DEBUG: DataLoadersHandler.execute - SeedsManager.import_seeds вернул: {seeds_import_success} (тип: {type(seeds_import_success)})") # 🔥 ДОБАВЛЕН ЛОГ
                
                if not seeds_import_success: # Проверяем результат импорта сидов
                    self.logger.critical("🚨 SeedsManager.import_seeds завершился неудачей. Прерываем DataLoadersHandler.")
                    return False # Возвращаем False, если импорт сидов не удался

                self.logger.info("✅ Seeds загружены в PostgreSQL.")
                self.logger.debug("DEBUG: DataLoadersHandler.execute - SeedsManager.import_seeds завершен. Запускаем ReferenceDataLoader.load_and_cache_all_data.")

                reference_data_load_success = await self._reference_data_loader.load_and_cache_all_data()
                self.logger.debug(f"DEBUG: DataLoadersHandler.execute - ReferenceDataLoader.load_and_cache_all_data вернул: {reference_data_load_success} (тип: {type(reference_data_load_success)})") # 🔥 ДОБАВЛЕН ЛОГ

                if not reference_data_load_success: # Проверяем результат загрузки справочных данных
                    self.logger.critical("🚨 ReferenceDataLoader.load_and_cache_all_data завершился неудачей. Прерываем DataLoadersHandler.")
                    return False # Возвращаем False, если загрузка справочных данных не удалась

                self.logger.info("✅ Справочные данные загружены и кэшированы в Redis.")
                self.logger.debug("DEBUG: DataLoadersHandler.execute - ReferenceDataLoader.load_and_cache_all_data завершен. Коммитим сессию.")

                await session.commit() # Коммит всех изменений в этой транзакции
                self.logger.info("✅ Шаг DataLoadersHandler успешно выполнен. Транзакция закоммичена.")
                self.logger.debug("DEBUG: DataLoadersHandler.execute - Коммит завершен. Возвращаем True.")
                return True # 🔥 КРИТИЧЕСКИ ВАЖНО: ЯВНЫЙ ВОЗВРАТ True

        except Exception as e:
            self.logger.critical(f"🚨 Не удалось создать или выполнить шаг 'DataLoadersHandler': {e}", exc_info=True)
            self.logger.critical("🚨 ОСТАНОВКА ПРЕДСТАРТА: Шаг 'DataLoadersHandler' завершился с ошибкой. Откат транзакции.")
            self.logger.debug("DEBUG: DataLoadersHandler.execute - Поймано исключение. Возвращаем False.") # 🔥 ИЗМЕНЕНО: Возвращаем False при исключении
            return False # 🔥 КРИТИЧЕСКИ ВАЖНО: ЯВНЫЙ ВОЗВРАТ False при исключении
