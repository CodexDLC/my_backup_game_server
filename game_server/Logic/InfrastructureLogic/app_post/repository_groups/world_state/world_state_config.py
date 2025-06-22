# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/world_state/world_state_config.py

# Импорты реализаций репозиториев из подгруппы core_world
from .core_world.game_location_repository_impl import GameLocationRepositoryImpl
from .core_world.state_entity_repository_impl import StateEntityRepositoryImpl

# Импорты реализаций репозиториев из подгруппы auto_session
from .auto_session.auto_session_repository_impl import AutoSessionRepositoryImpl
from .auto_session.xp_tick_data_repository_impl import XpTickDataRepositoryImpl


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import (
    IGameLocationRepository,
    IStateEntityRepository,
    IAutoSessionRepository,
    IXpTickDataRepository
)


# Конфигурация для группы репозиториев 'world_state'
world_state_repo_config = [
    {
        "name": "game_location_repository",
        "implementation": GameLocationRepositoryImpl,
        "interface": IGameLocationRepository
    },
    {
        "name": "state_entity_repository",
        "implementation": StateEntityRepositoryImpl,
        "interface": IStateEntityRepository
    },
    {
        "name": "auto_session_repository",
        "implementation": AutoSessionRepositoryImpl,
        "interface": IAutoSessionRepository
    },
    {
        "name": "xp_tick_data_repository",
        "implementation": XpTickDataRepositoryImpl,
        "interface": IXpTickDataRepository
    },
    # Если в будущем будут другие репозитории в этой группе или новых подгруппах, добавьте их сюда.
]