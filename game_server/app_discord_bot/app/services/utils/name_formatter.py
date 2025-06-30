# game_server/app_discord_bot/app/services/utils/name_formatter.py

import re
from typing import Dict, Any, Optional

from game_server.config.logging.logging_setup import app_logger as logger

class NameFormatter:
    """
    Утилитарный класс для форматирования и нормализации имен категорий и каналов Discord.
    Добавляет/удаляет эмодзи, префиксы и другие визуальные элементы,
    основываясь на конфигурации.
    """
    def __init__(self, emojis_formatting_config: Dict[str, Any]):
        """
        Инициализирует NameFormatter с загруженной конфигурацией эмодзи и форматирования.
        :param emojis_formatting_config: Словарь с правилами форматирования из emojis_formatting_config.json
        """
        self.emojis_formatting = emojis_formatting_config
        self.logger = logger
        self.logger.info("✨ NameFormatter инициализирован.")

        # Компилируем регулярные выражения для эффективной очистки
        # Регулярка для удаления эмодзи: ищет большинство стандартных эмодзи
        self._emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags (iOS)
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        # Регулярка для удаления префиксов типа "# ", "🔊 ", "💬 ", "📜 -" и т.д.
        # Собираем все возможные префиксы из конфига для удаления
        all_prefixes_to_clean = []
        if 'channel_formatting' in self.emojis_formatting:
            all_prefixes_to_clean.extend(self.emojis_formatting['channel_formatting'].values())
        if 'category_formatting' in self.emojis_formatting and 'default_prefix' in self.emojis_formatting['category_formatting']:
            all_prefixes_to_clean.append(self.emojis_formatting['category_formatting']['default_prefix'])
        # Добавляем специфические префиксы, если они используются вместе с эмодзи
        specific_emojis_combined_with_dash = [
            f"{re.escape(emoji)} -" # Эмодзи и тире
            for emoji in self.emojis_formatting.get('specific_channel_emojis', {}).values()
            if '-' in emoji # Пример: если эмодзи было "✅ -"
        ]
        all_prefixes_to_clean.extend(specific_emojis_combined_with_dash)
        
        # Убедимся, что '#' тоже чистится, если он идет в начале
        all_prefixes_to_clean.append(re.escape("# "))
        
        # Создаем единую регулярку для очистки всех известных префиксов
        # Сортируем от длинных к коротким, чтобы избежать частичных совпадений
        all_prefixes_to_clean = sorted(list(set(all_prefixes_to_clean)), key=len, reverse=True)
        self._prefix_pattern = re.compile(f"^(?:{'|'.join(map(re.escape, all_prefixes_to_clean))})")


    def _get_prefix_for_name(self, name: str, entity_type: str) -> str:
        """
        Возвращает префикс (эмодзи + форматирование) для имени сущности.
        Приоритет: специфический эмодзи по имени > дефолтный префикс по типу.
        """
        # Поиск специфического эмодзи для канала
        if entity_type in ['text_channel', 'voice_channel', 'forum', 'news']:
            specific_emoji = self.emojis_formatting.get('specific_channel_emojis', {}).get(name)
            if specific_emoji:
                return specific_emoji # Предполагаем, что specific_emoji уже включает нужный разделитель (например, "✅ -")
        
        # Поиск специфического эмодзи для категории
        elif entity_type == 'category':
            specific_emoji = self.emojis_formatting.get('specific_category_emojis', {}).get(name)
            if specific_emoji:
                return specific_emoji # Предполагаем, что specific_emoji уже включает нужный разделитель (например, "🏠 ")

        # Если нет специфического эмодзи, используем дефолтные префиксы по типу
        if entity_type == 'text_channel':
            return self.emojis_formatting.get('channel_formatting', {}).get('default_text_prefix', '# ')
        elif entity_type == 'voice_channel':
            return self.emojis_formatting.get('channel_formatting', {}).get('default_voice_prefix', '🔊 ')
        elif entity_type == 'forum':
            return self.emojis_formatting.get('channel_formatting', {}).get('default_forum_prefix', '💬 ')
        elif entity_type == 'news':
            return self.emojis_formatting.get('channel_formatting', {}).get('default_news_prefix', '📢 ')
        elif entity_type == 'category':
            return self.emojis_formatting.get('category_formatting', {}).get('default_prefix', '📁 ')
        
        return "" # Если тип не распознан, возвращаем пустую строку


    def format_name_for_discord(self, name: str, entity_type: str) -> str:
        """
        Форматирует "чистое" имя (из конфига) для отображения в Discord.
        Добавляет эмодзи и префиксы.
        :param name: Каноничное имя из JSON-конфигурации.
        :param entity_type: Тип сущности ('text_channel', 'category' и т.д.).
        :return: Имя, отформатированное для Discord.
        """
        if not name:
            return name

        prefix = self._get_prefix_for_name(name, entity_type)
        
        # Для каналов Discord автоматически приводит имя к нижнему регистру и заменяет пробелы на дефисы.
        # Поэтому мы должны подавать чистое имя, а не уже отформатированное.
        # Имя канала в Discord API не может содержать эмодзи, #, пробелы после # и т.д.
        # Но имя категории может.

        if entity_type == 'category':
            # Для категорий: добавляем префикс и сохраняем оригинальный регистр,
            # но очищаем от старых эмодзи/префиксов, если они случайно остались в name.
            cleaned_name = self.normalize_name_from_discord(name, entity_type) # Очищаем на всякий случай
            return f"{prefix}{cleaned_name}".strip()
        else: # Для каналов (text, voice, forum, news)
            # Discord API сам приводит имена каналов к нижнему регистру и меняет пробелы на дефисы.
            # Мы просто добавляем префикс в отображаемое имя (которое используется для поиска).
            # Настоящее имя для channel_kwargs['name'] не будет содержать эмодзи.
            # Тут логика сложнее, т.к. "форматирование" Discord-названий и "имя для API" разные.
            # Эта функция для get/utils.get, а не для create_channel(name=...)
            # Для create_channel, name= должен быть без эмодзи и в нижнем регистре с дефисами.
            return f"{prefix}{name}".strip()


    def normalize_name_from_discord(self, discord_name: str, entity_type: str) -> str:
        """
        Нормализует имя сущности, полученное из Discord, в "чистое" (каноничное) имя.
        Удаляет эмодзи, префиксы и лишние символы.
        :param discord_name: Имя, как оно отображается в Discord.
        :param entity_type: Тип сущности ('text_channel', 'category' и т.д.).
        :return: Каноничное имя, соответствующее JSON-конфигурации.
        """
        if not discord_name:
            return ""
        
        # Удаляем эмодзи
        cleaned_name = self._emoji_pattern.sub("", discord_name)
        
        # Удаляем известные префиксы (например, "# ", "🔊 ", "📜 -", "[ ")
        cleaned_name = self._prefix_pattern.sub("", cleaned_name).strip()

        # Для каналов Discord API сам приводит к нижнему регистру и заменяет пробелы на дефисы
        if entity_type in ['text_channel', 'voice_channel', 'forum', 'news']:
            # Удаляем возможное "#" в начале и приводим к чистому виду
            cleaned_name = cleaned_name.lstrip('#').replace('-', ' ').strip().lower()
        
        # Удаляем лишние скобки и пробелы для категорий, если они есть
        if entity_type == 'category':
            cleaned_name = cleaned_name.replace('[', '').replace(']', '').strip()
        
        # Дополнительная очистка: удаляем лишние пробелы и приводим к нижнему регистру для каналов
        return cleaned_name.strip().lower() if entity_type != 'category' else cleaned_name.strip()


# Пример использования (для внутреннего тестирования)
if __name__ == "__main__":
    # Предполагаемая структура конфигурации эмодзи
    test_emojis_config = {
        "channel_formatting": {
            "default_text_prefix": "# ",
            "default_voice_prefix": "🔊 ",
            "default_forum_prefix": "💬 ",
            "default_news_prefix": "📢 "
        },
        "category_formatting": {
            "default_prefix": "� "
        },
        "specific_channel_emojis": {
            "добро-пожаловать": "✅ -",
            "правила": "📜 -",
            "общий-чат": "🗣️ "
        },
        "specific_category_emojis": {
            "Категория: НАЧНИ ЗДЕСЬ": "👋 "
        }
    }

    formatter = NameFormatter(test_emojis_config)

    print("--- Форматирование для Discord ---")
    print(f"'добро-пожаловать' (text): '{formatter.format_name_for_discord('добро-пожаловать', 'text_channel')}'")
    print(f"'правила' (text): '{formatter.format_name_for_discord('правила', 'text_channel')}'")
    print(f"'общий-чат' (text): '{formatter.format_name_for_discord('общий-чат', 'text_channel')}'")
    print(f"'Категория: НАЧНИ ЗДЕСЬ' (category): '{formatter.format_name_for_discord('Категория: НАЧНИ ЗДЕСЬ', 'category')}'")
    print(f"'Новая Категория' (category): '{formatter.format_name_for_discord('Новая Категория', 'category')}'")
    print(f"'голос-чат' (voice): '{formatter.format_name_for_discord('голос-чат', 'voice_channel')}'")


    print("\n--- Нормализация из Discord ---")
    print(f"'✅ -добро-пожаловать' (text): '{formatter.normalize_name_from_discord('✅ -добро-пожаловать', 'text_channel')}'")
    print(f"'📜 -правила' (text): '{formatter.normalize_name_from_discord('📜 -правила', 'text_channel')}'")
    print(f"'🗣️ общий-чат' (text): '{formatter.normalize_name_from_discord('🗣️ общий-чат', 'text_channel')}'")
    print(f"'# общие-каналы' (text): '{formatter.normalize_name_from_discord('# общие-каналы', 'text_channel')}'")
    print(f"'👋 Категория: НАЧНИ ЗДЕСЬ' (category): '{formatter.normalize_name_from_discord('👋 Категория: НАЧНИ ЗДЕСЬ', 'category')}'")
    print(f"'[ ИГРОВОЙ ДОСТУП ]' (category): '{formatter.normalize_name_from_discord('[ ИГРОВОЙ ДОСТУП ]', 'category')}'")
    print(f"'Новая Категория' (category): '{formatter.normalize_name_from_discord('Новая Категория', 'category')}'")
    print(f"'🔊 голос-чат' (voice): '{formatter.normalize_name_from_discord('🔊 голос-чат', 'voice_channel')}'")
