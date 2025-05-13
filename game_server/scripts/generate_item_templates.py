import asyncio
from SQLAlchemy_config import AsyncSessionLocal
from game_server.database.models.models import (
    AccessoryTemplates,
    ArmorTemplates,
    WeaponTemplates,
)
from game_server.Logic.DomainLogic.ItemGenerator.generator_functions import (
    generate_accessories,
    generate_armor,
    generate_weapons,
)


async def generate_item_templates():
    # Открываем сессию и транзакцию
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # Очищаем старые записи в таблицах
            await session.execute("DELETE FROM accessory_templates")
            await session.execute("DELETE FROM armor_templates")
            await session.execute("DELETE FROM weapon_templates")

            # Генерация аксессуаров
            accessories = generate_accessories()  # генерируем данные
            for row in accessories:
                session.add(AccessoryTemplates(**row))

            # Генерация брони
            armors = generate_armor()
            for row in armors:
                session.add(ArmorTemplates(**row))

            # Генерация оружия
            weapons = generate_weapons()
            for row in weapons:
                session.add(WeaponTemplates(**row))

        # При выходе из блока транзакции — автоматически будет выполнен COMMIT

if __name__ == "__main__":
    asyncio.run(generate_item_templates())  # Запускаем генерацию
