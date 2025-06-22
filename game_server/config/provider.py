"""
Главный провайдер конфигурации.
"""

# --- Импорт всех модулей с константами ---
from .constants import character as character_constants
from .constants import coordinator as coordinator_constants
from .constants import generator as generator_constants
from .constants import item as item_constants
from .constants import redis as redis_constants
from .constants import seeds as seeds_constants
from .constants import arq as arq_constants


# --- Импорт всех модулей с настройками ---
from .settings.process import prestart as prestart_settings
from .settings.process import runtime as runtime_settings
from .settings import redis_setting as redis_settings_module
# 🔥 НОВЫЙ ИМПОРТ: Импортируем настройки генератора персонажей
from .settings.character import generator_settings as character_generator_settings


class _Constants:
    """Вложенный класс для группировки всех констант."""
    def __init__(self):
        self.character = character_constants
        self.coordinator = coordinator_constants
        self.generator = generator_constants
        self.item = item_constants
        self.redis = redis_constants
        self.seeds = seeds_constants
        self.arq = arq_constants
        
class _Settings:
    """Вложенный класс для группировки всех настроек."""
    def __init__(self):
        self.prestart = prestart_settings
        self.runtime = runtime_settings
        self.redis = redis_settings_module
        # 🔥 НОВОЕ: Добавляем настройки генератора персонажей
        self.character = character_generator_settings


class ConfigProvider:
    """
    Единая точка доступа ко всем игровым константам и настройкам.
    """
    def __init__(self):
        self.constants = _Constants()
        self.settings = _Settings()

# --- Создаем единственный экземпляр, который будет использоваться везде ---
config = ConfigProvider()