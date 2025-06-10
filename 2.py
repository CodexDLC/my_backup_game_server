import os
import asyncpg
import asyncio

# Настройки подключения к базе данных
DB_USER = "codexen"
DB_PASSWORD = "123"
DB_HOST = "192.168.137.1"
DB_PORT = "5432"
DB_NAME = "game_db"

SCHEMA_PATH = "game_server/database/schemas"

async def load_sql_files():
    conn = await asyncpg.connect(
        user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database=DB_NAME
    )

    for root, _, files in os.walk(SCHEMA_PATH):  # Проходим по всем подпапкам
        for filename in sorted(files):  # Сортируем файлы, если порядок важен
            if filename.endswith(".sql"):
                file_path = os.path.join(root, filename)
                print(f"🔹 Загружаю {file_path}")

                with open(file_path, "r", encoding="utf-8") as f:
                    sql_script = f.read()
                    await conn.execute(sql_script)  # Выполняем SQL

    await conn.close()
    print("✅ Все SQL-файлы загружены!")

asyncio.run(load_sql_files())
