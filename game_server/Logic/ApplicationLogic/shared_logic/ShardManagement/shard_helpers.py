# game_server/Logic/ApplicationLogic/shared_logic/ShardManagement/shard_helpers.py

import asyncio
import logging
from typing import Optional, List, Any # Добавляем List, Any для типизации GameShard объектов
from sqlalchemy.ext.asyncio import AsyncSession # Добавлен AsyncSession

# Импорты репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository

# Импортируем модель GameShard для типизации
from game_server.database.models.models import GameShard


logger = logging.getLogger(__name__)

# ИЗМЕНЕНИЕ: find_best_shard теперь принимает активные репозитории
async def find_best_shard(
    account_game_data_repo: IAccountGameDataRepository, # <--- Принимает активный репозиторий
    game_shard_repo: IGameShardRepository, # <--- Принимает активный репозиторий
) -> Optional[int]: # Возвращает int для discord_guild_id
    """
    Находит лучший доступный шард, получая данные о количестве игроков напрямую из БД.
    """
    
    # Ищем самый свободный из всех
    all_shards: List[GameShard] = await game_shard_repo.get_all_active_shards() # Используем переданный репозиторий
    if not all_shards:
        logger.warning("Нет доступных активных шардов в БД.")
        return None

    best_shard_id = None
    min_players = float('inf')

    for shard in all_shards:
        current_players = shard.current_players
        free_slots = shard.max_players - current_players
        
        if shard.is_system_active and free_slots > 0 and current_players < min_players:
            min_players = current_players
            best_shard_id = shard.discord_guild_id

    if best_shard_id is not None:
        logger.info(f"Найден лучший шард: {best_shard_id} с {min_players} игроками.")
        return best_shard_id
    else:
        logger.warning(f"Не удалось найти подходящий шард. Все шарды переполнены или недоступны.")
        return None


async def _is_shard_available(
    game_shard_repo: IGameShardRepository, # <--- Принимает активный репозиторий
    discord_guild_id: int
) -> bool:
    """ Проверяет, есть ли место на конкретном шарде (получая данные из БД). """
    shard_info: Optional[GameShard] = await game_shard_repo.get_shard_by_guild_id(discord_guild_id) # Используем переданный репозиторий
    if not shard_info or not shard_info.is_system_active:
        return False
    
    current_players = shard_info.current_players
    return current_players < shard_info.max_players


async def finalize_assignment(
    account_game_data_repo: IAccountGameDataRepository, # <--- Принимает активный репозиторий
    account_id: int, 
    shard_id_int: int
):
    """ Привязывает игрока к шарду в БД и обновляет счетчик в БД. """
    await account_game_data_repo.update_shard_id(account_id, shard_id_int) # Используем переданный репозиторий
    logger.info(f"Игрок {account_id} успешно привязан к шарду {shard_id_int}.")


def trigger_cleanup_cycle():
    """
    Отправляет задачу на очистку "мертвых душ" в очередь для воркера.
    """
    logger.warning("Свободных шардов нет. Отправка задачи на очистку 'мертвых душ' воркеру...")
    # TODO: Здесь будет код для отправки задачи в ARQ или другую систему очередей.
    pass