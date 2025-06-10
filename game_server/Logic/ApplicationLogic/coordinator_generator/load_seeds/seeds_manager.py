import logging
from pathlib import Path
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.seed_constants import FILE_LOAD_ORDER
from game_server.database.models.models import Base
# Добавлено для Base.registry.mappers

# ИСПРАВЛЕНО: Импортируем SeedLoader (как вы подтвердили)
from .seed_loader import SeedLoader
from .seeds_config import SeedsConfig # Предполагается, что SeedsConfig определен
from game_server.services.logging.logging_setup import logger # Глобальный логгер

# Удалена настройка логирования logging.basicConfig

class SeedsManager:
    

    # ИСПРАВЛЕНО: Конструктор принимает сессию, как в вашей "рабочей" версии
    def __init__(self, session: AsyncSession):
        logger.info("✅ Инициализация SeedsManager...") # Используем глобальный логгер
        self.session = session # Сохраняем сессию
        # ИСПРАВЛЕНО: SeedLoader инициализируется с переданной сессией
        self.loader = SeedLoader(self.session)

        # ИСПРАВЛЕНО: Инициализация all_models_map для SQLAlchemy 2.0
        self.all_models_map = {cls.__name__: cls for cls in Base.registry.mappers if hasattr(cls, '__tablename__')}
        logger.info(f"SeedsManager инициализирован. Загружено моделей: {len(self.all_models_map)}")
        # Добавлены глобальные счетчики для этого менеджера
        self.inserted_total = 0
        self.updated_total = 0


    @classmethod
    def convert_filename_to_model(cls, filename: str) -> str:
        """Конвертирует имя файла в название модели"""
        name = filename.replace('.yml', '')
        if '_' in name and name.split('_')[0].isdigit():
            name = '_'.join(name.split('_')[1:])
        model_name = ''.join(word.capitalize() for word in name.split('_'))
        logger.debug(f"🔄 Конвертация файла '{filename}' → модель '{model_name}'") # Используем глобальный логгер
        return model_name

    async def import_seeds(self, models_module):
        """Запускает процесс импорта seed-данных"""
        logger.info("🚀 Запуск импорта seed-файлов...") # Используем глобальный логгер
        
        # Получаем отсортированные файлы
        seed_files = self._collect_seed_files()

        if not seed_files:
            logger.warning("⚠️ Нет файлов для загрузки! Проверь SEEDS_DIR.") # Используем глобальный логгер
            return

        for file_path in seed_files:
            model_name = self.convert_filename_to_model(file_path.name)
            model = getattr(models_module, model_name, None)

            if not model:
                logger.warning(f"⚠️ Модель '{model_name}' не найдена! Файл '{file_path}' пропускается.") # Используем глобальный логгер
                continue

            logger.debug(f"📂 Обрабатываем файл '{file_path}' для модели '{model_name}'")
            inserted, updated = await self.loader.process_seed_file(file_path, model)
            # Суммируем результаты от SeedLoader в общих счетчиках SeedsManager
            self.inserted_total += inserted
            self.updated_total += updated

        logger.info(f"✅ Импорт завершён. Всего вставлено: {self.inserted_total}, обновлено: {self.updated_total}") # Используем глобальный логгер

    def _collect_seed_files(self) -> list[Path]:
        """Собирает все .yml файлы, включая вложенные папки,
           сперва по заданному порядку, затем остальные."""
        logger.info(f"📌 Ищем seed-файлы внутри {SeedsConfig.SEEDS_DIR}...")

        all_yml_files = list(SeedsConfig.SEEDS_DIR.rglob('*.yml'))
        
        # 1. Файлы, которые есть в FILE_LOAD_ORDER (теперь импортируется)
        ordered_files = []
        ordered_file_names = set(FILE_LOAD_ORDER) # Используем импортированный FILE_LOAD_ORDER
        
        file_paths_by_name = {f.name: f for f in all_yml_files}

        for name in FILE_LOAD_ORDER: # Используем импортированный FILE_LOAD_ORDER
            if name in file_paths_by_name:
                ordered_files.append(file_paths_by_name[name])
            else:
                logger.warning(f"⚠️ Файл '{name}' из FILE_LOAD_ORDER не найден в SEEDS_DIR.")

        # 2. Остальные файлы (не попавшие в FILE_LOAD_ORDER)
        remaining_files = []
        for f in all_yml_files:
            if f.name not in ordered_file_names:
                remaining_files.append(f)
        
        remaining_files.sort(key=lambda x: x.name)

        final_file_list = ordered_files + remaining_files

        if not final_file_list:
            logger.warning("⚠️ Нет .yml файлов в SEEDS_DIR, включая подпапки!")

        logger.info(f"✅ Найдено {len(final_file_list)} файлов для загрузки (с приоритетом из FILE_LOAD_ORDER).")
        logger.debug(f"Порядок загрузки: {[f.name for f in final_file_list]}")

        return final_file_list