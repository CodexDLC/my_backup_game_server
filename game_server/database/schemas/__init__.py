import os
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

schemas_dir = "game_server/database/schemas"

async def load_sql_files(session: AsyncSession):
    async with session.begin():
        for root, _, files in os.walk(schemas_dir):
            for file in files:
                if file.endswith(".sql"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        sql_script = f.read()

                    # Разбиваем SQL-скрипт на отдельные выражения по символу ";"
                    # Это простое разбиение; для более сложных случаев можно использовать специализированный парсер.
                    statements = sql_script.split(';')
                    for stmt in statements:
                        stmt = stmt.strip()
                        if stmt:
                            await session.execute(text(stmt))
