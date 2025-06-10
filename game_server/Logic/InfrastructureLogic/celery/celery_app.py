
# game_server\Logic\InfrastructureLogic\celery\celery_app.py

from celery import Celery
from celery.signals import after_setup_logger
from dotenv import load_dotenv

from game_server.settings import CELERY_BROKER_URL, CELERY_RESULT_BACKEND

# --- Импортируем ваши компоненты для настройки логирования ---
from game_server.services.logging.logging_config import loggerConfig
from game_server.services.logging.logging_handlers import get_console_handler, get_file_handler


# Загружаем переменные окружения
load_dotenv()

app = Celery("game_server",
             broker=CELERY_BROKER_URL, # Используем импортированный URL брокера
             backend=CELERY_RESULT_BACKEND) # Используем импортированный URL бэкенда

# --- ▼▼▼ ФИНАЛЬНЫЙ КОД ДЛЯ УНИФИКАЦИИ ЛОГОВ ▼▼▼ ---
@after_setup_logger.connect

def setup_celery_loggers(logger, **kwargs):
    """
    Эта функция перехватывает логгер Celery после его инициализации
    и полностью перенастраивает его, используя нашу кастомную конфигурацию.
    """
    # 1. Очищаем все стандартные обработчики, которые Celery мог добавить
    logger.handlers.clear()

    # 2. Создаем экземпляр нашей конфигурации
    config = loggerConfig()

    # 3. Добавляем все наши файловые и консольные обработчики к логгеру Celery
    logger.addHandler(get_console_handler(config.console_log_level))
    logger.addHandler(get_file_handler(config.debug_log_file, config.debug_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.info_log_file, config.info_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.warning_log_file, config.warning_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.error_log_file, config.error_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.critical_log_file, config.critical_log_level, config.max_file_size, config.backup_count))
    logger.addHandler(get_file_handler(config.exception_log_file, config.exception_log_level, config.max_file_size, config.backup_count))

    # 4. Устанавливаем общий уровень для самого логгера (он будет пропускать все, 
    # а фильтровать будут уже сами обработчики)
    logger.setLevel(config.debug_log_level) # Ставим самый низкий уровень, чтобы ничего не пропустить

# --- ▲▲▲ КОНЕЦ НОВОГО КОДА ▲▲▲ ---

# Создание Celery-приложения


# Загружаем конфиг из `game_server/config/celery_config.py`
app.config_from_object("game_server.Logic.InfrastructureLogic.celery.celery_config", namespace="CELERY")

# Автоматически ищем задачи в `game_server/celery`
app.autodiscover_tasks(["game_server.Logic.InfrastructureLogic.celery.task"])

app.conf.update(
    include=[
        "game_server.Logic.InfrastructureLogic.celery.task.tasks_character_generation",
        "game_server.Logic.InfrastructureLogic.celery.task.tasks_item_generation",        
    ]
)

