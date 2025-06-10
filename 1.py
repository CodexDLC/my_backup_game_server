import os
import re
import shutil

# Путь к файлу `models.py`
MODELS_FILE = "game_server/database/models/models.py"
OUTPUT_DIR = "game_server/database/models/"

# Стандартные импорты
STANDARD_IMPORTS = """from sqlalchemy import Column, Integer, String, SmallInteger, BigInteger, JSON, Text, ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped
from typing import List, Optional
from .base import Base  # Импорт базовой модели
"""

# Читаем содержимое `models.py`
with open(MODELS_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# Регулярное выражение для поиска классов
model_pattern = re.findall(r"class (\w+)\(Base\):(.+?)(?=\nclass |\Z)", content, re.DOTALL)

# Создаём папку `models/` если её нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Список моделей для `__init__.py`
models_list = []

for model_name, model_code in model_pattern:
    models_list.append(model_name)
    
    # Создаём файл для модели
    model_file = os.path.join(OUTPUT_DIR, f"{model_name.lower()}.py")
    with open(model_file, "w", encoding="utf-8") as f:
        f.write(STANDARD_IMPORTS + "\n\nfrom .base import Base\n\nclass {model_name}(Base):{model_code}\n")

# Обновляем `__init__.py`
init_file = os.path.join(OUTPUT_DIR, "__init__.py")
with open(init_file, "w", encoding="utf-8") as f:
    f.write("\n".join(f"from .{name.lower()} import {name}" for name in models_list))

print("✅ Разделение моделей завершено и стандартные импорты добавлены!")
