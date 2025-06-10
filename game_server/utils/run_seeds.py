# game_server\utils\run_seeds.py

import asyncio
# Убедитесь, что 'engine' импортируется из вашего проекта, например:

# Добавьте импорт вашей фабрики сессий, используемой в проекте:
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal

from game_server.database.models import models
# Путь к SeedsManager обновлен вами
from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.seeds_manager import SeedsManager 

async def main():
    # Вместо AsyncSession(engine) напрямую используем AsyncSessionLocal()
    async with AsyncSessionLocal() as session: 
        manager = SeedsManager(session)
        await manager.import_seeds(models)

if __name__ == "__main__":
    asyncio.run(main())