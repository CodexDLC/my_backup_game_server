# game_server\Logic\ApplicationLogic\world_orchestrator\workers\world_map_generator\arq_world_map_generation.py

import logging
from typing import Dict, Any, Callable
# import inject # 🔥 УДАЛЕНО: inject больше не нужен для autoparams здесь
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем наш transactional декоратор
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

# Импорты классов/интерфейсов, которые будут получены из ctx
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.world_map_generator.world_map_generator import WorldMapGenerator
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository, IWorldStateRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader


from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal


# 🔥 УДАЛЕНО: @inject.autoparams() полностью
@transactional(AsyncSessionLocal)
async def generate_world_map_task(
    session: AsyncSession, # <--- Сессия от @transactional
    ctx: Dict[str, Any],    # <--- Контекст ARQ (теперь используем его для зависимостей)
    job_id: str,            # <--- job_id от ARQ
    **kwargs,               # Для любых дополнительных аргументов ARQ
) -> bool:
    """
    ARQ-задача для генерации и сохранения статического "скелета" карты мира.
    Генератор работает с полным набором данных напрямую, без промежуточного payload.
    Вся операция обернута в единую транзакцию.
    """
    # 🔥 ИЗМЕНЕНИЕ: Получаем зависимости из ctx
    logger: logging.Logger = ctx["logger"]
    pg_location_repo_factory: Callable[[AsyncSession], IGameLocationRepository] = ctx["pg_location_repo_factory"]
    mongo_world_repo: IWorldStateRepository = ctx["mongo_world_repo"]
    location_state_repo: ILocationStateRepository = ctx["location_state_repo"]
    redis_reader: ReferenceDataReader = ctx["redis_reader"]


    log_prefix = f"WORLD_MAP_GEN_TASK (ID: {job_id}):"
    logger.info(f"{log_prefix} Запуск задачи по генерации карты мира (транзакционно).")

    try:
        # Создаем экземпляр репозитория PostgreSQL с активной сессией, переданной декоратором
        pg_location_repo = pg_location_repo_factory(session)

        # 2. Создаем экземпляр генератора карты
        world_generator = WorldMapGenerator(
            pg_location_repo=pg_location_repo,
            mongo_world_repo=mongo_world_repo,
            location_state_repo=location_state_repo,
            redis_reader=redis_reader,
            logger=logger
        )

        # 3. Запускаем процесс сборки и сохранения
        success = await world_generator.generate_and_store_world_map()

        if success:
            logger.info(f"{log_prefix} ✅ Задача по генерации карты мира успешно завершена.")
        else:
            logger.error(f"{log_prefix} ❌ Задача по генерации карты мира завершилась с ошибкой.")

        return success

    except Exception as e:
        logger.critical(f"{log_prefix} 🚨 Критическая ошибка в задаче генерации карты: {e}", exc_info=True)
        raise