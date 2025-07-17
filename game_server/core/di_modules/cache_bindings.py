# game_server/core/di_modules/cache_bindings.py



# Импорты менеджеров кэша
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.services.character.character_cache_manager import CharacterCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.item.item_cache_manager import ItemCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.discord.backend_guild_config_manager import BackendGuildConfigManager
from game_server.Logic.InfrastructureLogic.app_cache.services.session.session_manager import RedisSessionManager

# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_session_cache import ISessionManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_item_cache import IItemCacheManager # 🔥 ДОБАВЛЕНО: Импорт интерфейса ItemCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager # 🔥 ДОБАВЛЕНО: Импорт интерфейса ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_backend_guild_config import IBackendGuildConfigManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_character_cache import ICharacterCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_redis_batch_store import IRedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_shard_count_cache import IShardCountCacheManager


def configure_cache_managers(binder):
    """
    Конфигурирует связывания для всех менеджеров кэша.
    Все они теперь будут получать CentralRedisClient и Logger через inject.autoparams.
    Привязки сделаны для интерфейсов, где это возможно, и для конкретных классов.
    """
    # Привязываем конкретные реализации (как они будут создаваться)
    binder.bind_to_constructor(IShardCountCacheManager, ShardCountCacheManager)
    binder.bind_to_constructor(IRedisBatchStore, RedisBatchStore)
    binder.bind_to_constructor(ICharacterCacheManager, CharacterCacheManager)
    binder.bind_to_constructor(IItemCacheManager, ItemCacheManager)
    binder.bind_to_constructor(IReferenceDataCacheManager, ReferenceDataCacheManager)
    binder.bind_to_constructor(IReferenceDataReader, ReferenceDataReader)
    binder.bind_to_constructor(IBackendGuildConfigManager, BackendGuildConfigManager)
    binder.bind_to_constructor(ISessionManager, RedisSessionManager)




