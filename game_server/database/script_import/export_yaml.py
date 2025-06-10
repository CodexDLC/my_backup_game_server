import yaml
import asyncio
import os

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.database import models

async def export_to_yaml(schema: str):
    """ Экспорт данных из указанной схемы в YAML в папку `import_{schema}` с готовым подключением к БД. """
    class_name = schema.title().replace("_", "")  # Преобразуем имя схемы в название ORM-класса
    model = getattr(models, class_name, None)  # Получаем класс модели

    if not model:
        print(f"⚠️ Ошибка: Модель {class_name} не найдена.")
        return

    async with AsyncSessionLocal() as session:  # ✅ Используем готовое подключение
        result = await session.execute(model.select())
        data = [row._asdict() for row in result.fetchall()]  # Преобразуем строки в словари

    yaml_data = {"version": "1.0", "schema": schema, "data": data}

    # 🔹 Создаём папку `import_{schema}`
    output_dir = os.path.join(os.path.dirname(__file__), f"import_{schema}")
    os.makedirs(output_dir, exist_ok=True)

    filename = os.path.join(output_dir, f"{schema}.yml")
    with open(filename, "w", encoding="utf-8") as file:
        yaml.dump(yaml_data, file, default_flow_style=False)

    print(f"✅ Экспорт завершён: {filename}")


# 🔹 Запуск с аргументом `schema`
async def main():
    schema = input("Введите schema для экспорта: ").strip()
    await export_to_yaml(schema)

if __name__ == "__main__":
    asyncio.run(main())
