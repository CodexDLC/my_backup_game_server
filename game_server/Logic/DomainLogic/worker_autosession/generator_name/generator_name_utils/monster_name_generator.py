# game_server/Logic/InfrastructureLogic/generator/name_generator/monster_name_generator.py

import random
from typing import List

class MonsterNameGenerator:
    """
    Класс для генерации имен монстров.
    """
    _MONSTER_NAMES: List[str] = [
        "Громозев", "Клыкастый", "Злобень", "Рычун", "Теневой", "Болотник",
        "Камнерог", "Когтерез", "Глубинник", "Острозуб", "Шепот леса", "Пожиратель душ",
        "Паук-плевун", "Огр-крушитель", "Лесной дух", "Пещерный червь"
    ]
    _MONSTER_SUFFIXES: List[str] = ["", " - Альфа", " - Страж", " - Древний", " - Вожак", " - Свирепый"]

    @classmethod
    def generate_name(cls, monster_type_hint: str = "") -> str:
        """
        Генерирует случайное имя монстра.
        Args:
            monster_type_hint (str): Подсказка о типе монстра (пока не используется для сложной логики,
                                    но может быть расширено).
        Returns:
            str: Сгенерированное имя монстра.
        """
        base_name = random.choice(cls._MONSTER_NAMES)
        suffix = random.choice(cls._MONSTER_SUFFIXES)
        return f"{base_name}{suffix}".strip()