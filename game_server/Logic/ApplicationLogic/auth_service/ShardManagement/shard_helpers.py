# game_server\Logic\ApplicationLogic\auth_service\ShardManagement\shard_helpers.py

import asyncio
import logging
from typing import Optional

from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager

logger = logging.getLogger(__name__)

async def find_best_shard(
    repo_manager: RepositoryManager, 
    shard_count_manager: ShardCountCacheManager,
    preferred_shard_id: str | None = None
) -> Optional[str]:
    """
    Находит лучший доступный шард. Сначала проверяет предпочтительный, затем ищет любой другой.
    """
    # Сначала проверяем предпочтительный шард, если он указан
    if preferred_shard_id:
        is_available = await _is_shard_available(repo_manager, shard_count_manager, preferred_shard_id)
        if is_available:
            return preferred_shard_id
    
    # Ищем самый свободный из всех
    all_shards = await repo_manager.game_shards.get_all_active_shards()
    shard_counts = await shard_count_manager.get_all_shards_player_count()

    best_shard = None
    max_free_slots = -1

    for shard in all_shards:
        current_players = shard_counts.get(str(shard.discord_guild_id), 0) # guild_id может быть int
        free_slots = shard.max_players - current_players
        if free_slots > max_free_slots:
            max_free_slots = free_slots
            best_shard = shard
    
    return str(best_shard.discord_guild_id) if best_shard and max_free_slots > 0 else None


async def _is_shard_available(
    repo_manager: RepositoryManager, 
    shard_count_manager: ShardCountCacheManager,
    shard_id: str
) -> bool:
    """ Проверяет, есть ли место на конкретном шарде. """
    shard_info = await repo_manager.game_shards.get_shard_by_guild_id(int(shard_id))
    if not shard_info or not shard_info.is_system_active:
        return False
    
    current_players = await shard_count_manager.get_shard_player_count(shard_id)
    return current_players < shard_info.max_players


async def finalize_assignment(
    repo_manager: RepositoryManager, 
    shard_count_manager: ShardCountCacheManager,
    account_id: int, 
    shard_id: str
):
    """ Привязывает игрока к шарду в БД и обновляет счетчик в Redis. """
    await repo_manager.account_game_data.update_shard_id(account_id, shard_id)
    await shard_count_manager.increment_shard_player_count(shard_id)
    logger.info(f"Игрок {account_id} успешно привязан к шарду {shard_id}.")


def trigger_cleanup_cycle():
    """
    Отправляет задачу на очистку "мертвых душ" в очередь для воркера.
    Немедленно возвращает управление, не дожидаясь выполнения.
    """
    logger.warning("Свободных шардов нет. Отправка задачи на очистку 'мертвых душ' воркеру...")
    # TODO: Здесь будет код для отправки задачи в ARQ или другую систему очередей.
    # Например: await arq_pool.enqueue_job('cleanup_inactive_players_task')
    pass