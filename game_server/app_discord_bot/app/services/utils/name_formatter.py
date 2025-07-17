# game_server/app_discord_bot/app/services/utils/name_formatter.py

import re
import logging
import inject
# 1. Добавьте Annotated из typing
from typing import Dict, Any, Annotated

class NameFormatter:
    # Убираем декоратор @inject.autoparams()
    def __init__(self, emojis_formatting_config: Dict[str, Any], logger: logging.Logger):
        self.emojis_formatting = emojis_formatting_config
        self.logger = logger
        self.logger.info("✨ NameFormatter инициализирован (создан вручную).")

        # Компилируем регулярные выражения для эффективной очистки
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
        all_prefixes_to_clean = []
        if 'channel_formatting' in self.emojis_formatting:
            all_prefixes_to_clean.extend(self.emojis_formatting['channel_formatting'].values())
        if 'category_formatting' in self.emojis_formatting and 'default_prefix' in self.emojis_formatting['category_formatting']:
            all_prefixes_to_clean.append(self.emojis_formatting['category_formatting']['default_prefix'])
        specific_emojis_combined_with_dash = [
            f"{re.escape(emoji)} -"
            for emoji in self.emojis_formatting.get('specific_channel_emojis', {}).values()
            if '-' in emoji
        ]
        all_prefixes_to_clean.extend(specific_emojis_combined_with_dash)
        
        all_prefixes_to_clean.append(re.escape("# "))
        
        all_prefixes_to_clean = sorted(list(set(all_prefixes_to_clean)), key=len, reverse=True)
        self._prefix_pattern = re.compile(f"^(?:{'|'.join(map(re.escape, all_prefixes_to_clean))})")


    def _get_prefix_for_name(self, name: str, entity_type: str) -> str:
        """
        Возвращает префикс (эмодзи + форматирование) для имени сущности.
        Приоритет: специфический эмодзи по имени > дефолтный префикс по типу.
        """
        if entity_type in ['text_channel', 'voice_channel', 'forum', 'news']:
            specific_emoji = self.emojis_formatting.get('specific_channel_emojis', {}).get(name)
            if specific_emoji:
                return specific_emoji
        
        elif entity_type == 'category':
            specific_emoji = self.emojis_formatting.get('specific_category_emojis', {}).get(name)
            if specific_emoji:
                return specific_emoji

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
        
        return ""


    def format_name_for_discord(self, name: str, entity_type: str) -> str:
        """
        Форматирует "чистое" имя (из конфига) для отображения в Discord.
        Добавляет эмодзи и префиксы.
        """
        if not name:
            return name

        prefix = self._get_prefix_for_name(name, entity_type)
        
        if entity_type == 'category':
            cleaned_name = self.normalize_name_from_discord(name, entity_type)
            return f"{prefix}{cleaned_name}".strip()
        else:
            return f"{prefix}{name}".strip()


    def normalize_name_from_discord(self, discord_name: str, entity_type: str) -> str:
        """
        Нормализует имя сущности, полученное из Discord, в "чистое" (каноничное) имя.
        Удаляет эмодзи, префиксы и лишние символы.
        """
        if not discord_name:
            return ""
        
        cleaned_name = self._emoji_pattern.sub("", discord_name)
        
        cleaned_name = self._prefix_pattern.sub("", cleaned_name).strip()

        if entity_type in ['text_channel', 'voice_channel', 'forum', 'news']:
            cleaned_name = cleaned_name.lstrip('#').replace('-', ' ').strip().lower()
        
        if entity_type == 'category':
            cleaned_name = cleaned_name.replace('[', '').replace(']', '').strip()
        
        return cleaned_name.strip().lower() if entity_type != 'category' else cleaned_name.strip()


