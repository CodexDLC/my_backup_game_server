# -*- coding: utf-8 -*-
from typing import List

# ======================================================================
# --- ПОРЯДОК ЗАГРУЗКИ ФАЙЛОВ С НАЧАЛЬНЫМИ ДАННЫМИ (SEEDS) ---
# ======================================================================
# Порядок в этом списке критически важен из-за зависимостей
# между данными в разных файлах.

FILE_LOAD_ORDER: List[str] = [
    # 000_system/002_state_entities
    'state_entity.yml',

    # character
    'background_story.yml',
    'personality.yml',
    'skills.yml',

    # item
    'Modifier_Library.yml',
    '001_Material.yml',
    '002_Material.yml',
    '003_Material.yml',
    '004_Material.yml',
    '005_Material.yml',
    '006_Material.yml',
    '001_suffix.yml',
    '002_suffix.yml',
    '003_suffix.yml',
    '004_suffix.yml',
    '005_suffix.yml',

    # creature_type
    '001_creature_type.yml',
]


from pathlib import Path

# ======================================================================
# --- ПУТИ И СТРУКТУРНЫЕ КОНСТАНТЫ ДЛЯ SEEDS ---
# ======================================================================

# Путь к корневой директории с seed-файлами
SEEDS_DIR = Path("game_server/database/seeds")

# Словарь для переопределения первичных ключей для конкретных моделей.
# Используется, когда PK не является стандартным 'id'.
# Ключ - имя класса модели (Model.__name__), значение - имя колонки PK.
MODEL_PK_OVERRIDES: dict[str, str] = {
    'QuestSteps': 'step_key'
}