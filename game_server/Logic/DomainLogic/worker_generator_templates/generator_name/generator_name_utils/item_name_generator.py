# game_server/Logic/InfrastructureLogic/generator/name_generator/item_name_generator.py

import re
from typing import Optional

class ItemNameGenerator:
    """
    Класс для генерации имен предметов.
    Генерирует имя на основе полученных компонентов, учитывая правила редкости/материала
    и форматируя регистр слов.
    """

    @classmethod
    def _format_initial_word(cls, text: str) -> str:
        """
        Приводит первое слово в строке к заглавной букве, остальные к нижнему регистру,
        и обрабатывает специфические предлоги (of, the, and, in) чтобы они были строчными.
        """
        if not text:
            return ""
        words = text.split()
        if not words:
            return ""

        formatted_words = [words[0].capitalize()]
        for i, word in enumerate(words[1:]):
            # Проверяем на все заглавные (акронимы или аббревиатуры)
            if word.upper() == word and len(word) > 1:
                formatted_words.append(word)
            else:
                formatted_words.append(word.lower())
        
        result = " ".join(formatted_words)
        # Обработка предлогов
        result = re.sub(r'\b(Of|The|And|In|With|For|From)\b', lambda m: m.group(0).lower(), result)
        
        return result

    # --- МЕТОД _desanitize_and_format_base_name УДАЛЯЕТСЯ ---


    @classmethod
    def generate_name(
        cls,
        rarity_prefix: Optional[str],
        base_item_display_name: str, # Теперь это оригинальное имя из YAML (например, "Simple Hood")
        material_adjective: str,
        suffix_fragment: Optional[str] = None
    ) -> str:
        """
        Генерирует читаемое имя предмета на основе его компонентов и заданных правил,
        форматируя регистр слов.
        """
        parts = []

        # 1. Первая часть имени (Редкость или Материал)
        if rarity_prefix and rarity_prefix.strip():
            parts.append(rarity_prefix.strip())
            # Если есть префикс редкости, материал будет после него
            if material_adjective and material_adjective.strip() and \
               material_adjective.lower() not in ["basic", "common", "standard"]:
                parts.append(cls._format_initial_word(material_adjective))
            # Отформатированное базовое имя будет идти как следующее слово
            formatted_base_name = cls._format_initial_word(base_item_display_name) # Применяем форматирование
            # Отформатированный суффикс
            suffix_formatted = cls._format_initial_word(suffix_fragment) if suffix_fragment else None
        else:
            # Если нет префикса редкости, материал будет первой частью
            if material_adjective and material_adjective.strip() and \
               material_adjective.lower() not in ["basic", "common", "standard"]:
                parts.append(material_adjective.strip().capitalize()) # Материал как первое слово, если он есть
            
            # Отформатированное базовое имя
            formatted_base_name = cls._format_initial_word(base_item_display_name) # Применяем форматирование
            # Отформатированный суффикс
            suffix_formatted = cls._format_initial_word(suffix_fragment) if suffix_fragment else None
        
        # Если parts все еще пуст, это значит, что нет ни редкости, ни "нестандартного" материала.
        # В этом случае, formatted_base_name должен стать первой частью и быть с большой буквы.
        # Если formatted_base_name уже был добавлен, то он уже отформатирован.
        if not parts and formatted_base_name:
            parts.append(formatted_base_name.capitalize()) # Убедимся, что первое слово с большой буквы

        # Добавляем остальные части (если они не были добавлены ранее в зависимости от логики parts.append)
        # Убедимся, что formatted_base_name не добавлен дважды
        if formatted_base_name and formatted_base_name not in parts:
            parts.append(formatted_base_name)

        # 3. Добавляем отформатированный фрагмент суффикса (если он есть)
        if suffix_formatted:
            # Проверяем, начинается ли суффикс уже с "of ", чтобы избежать "of of "
            if not suffix_formatted.lower().startswith("of "):
                parts.append(f"of {suffix_formatted.strip()}")
            else:
                parts.append(suffix_formatted.strip())

        final_name = " ".join(part for part in parts if part).strip()
        
        # Окончательная очистка от двойных пробелов, если они появились
        return re.sub(r'\s+', ' ', final_name).strip()