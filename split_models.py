import os
import re

# Определяем корень проекта
ROOT = os.path.dirname(os.path.abspath(__file__))

# Пути
SCHEMAS_BASE = os.path.join(ROOT, "game_server", "database", "schemas")
MODELS_FILE   = os.path.join(ROOT, "models.py")
OUTPUT_BASE   = os.path.join(ROOT, "models")

# 1. Собираем динамически группы по подпапкам SQL
GROUPS = {}
for entry in os.listdir(SCHEMAS_BASE):
    grp_path = os.path.join(SCHEMAS_BASE, entry)
    if os.path.isdir(grp_path):
        grp_name = entry.split("_", 1)[-1]  # "001_meta" -> "meta"
        GROUPS[grp_name] = []
        for root, _, files in os.walk(grp_path):
            for fn in files:
                if fn.endswith(".sql"):
                    GROUPS[grp_name].append(fn[:-4])

# Добавляем "others" для всего остального
GROUPS["others"] = []

print("Группы и таблицы по ним:", GROUPS)

# 2. Создаём папки и __init__.py
for grp in GROUPS:
    outdir = os.path.join(OUTPUT_BASE, grp)
    os.makedirs(outdir, exist_ok=True)
    initf = os.path.join(outdir, "__init__.py")
    open(initf, "a").close()

# 3. Читаем общий models.py
text = open(MODELS_FILE, "r", encoding="utf-8").read()

# 4. Парсим все блоки классов
blocks = re.findall(r"(?m)^class\s+\w+\(Base\):[\s\S]*?(?=^class\s+\w+\(Base\):|\Z)", text)

print(f"Найдено блоков классов: {len(blocks)}")

# 5. Разбиваем и складываем
for blk in blocks:
    m = re.search(r"__tablename__\s*=\s*['\"](\w+)['\"]", blk)
    if not m:
        continue
    tbl = m.group(1)
    placed = False
    for grp, tbls in GROUPS.items():
        if grp != "others" and tbl in tbls:
            dest = grp
            placed = True
            break
    if not placed:
        dest = "others"
    out_path = os.path.join(OUTPUT_BASE, dest, f"{tbl}.py")
    with open(out_path, "w", encoding="utf-8") as o:
        o.write("from ..models import Base\n\n")
        o.write(blk)
    print(f"– {tbl} → models/{dest}/{tbl}.py")
