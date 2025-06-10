
import os
schemas_dir = os.path.join(os.getcwd(), "game_server", "database", "schemas")
print(schemas_dir)
import sqlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

async def load_sql_files(session: AsyncSession):
    if not os.path.exists(schemas_dir):
        raise FileNotFoundError(f"Директория {schemas_dir} не найдена!")

    async with session.begin_nested():  # Используем вложенные транзакции
        for root, _, files in os.walk(schemas_dir):
            for file in files:
                if file.endswith(".sql"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                    # Корректное разбиение SQL-скрипта
                    statements = sqlparse.split(sql_script)
                    for stmt in statements:
                        stmt = stmt.strip()
                        if stmt:
                            await session.execute(text(stmt))
