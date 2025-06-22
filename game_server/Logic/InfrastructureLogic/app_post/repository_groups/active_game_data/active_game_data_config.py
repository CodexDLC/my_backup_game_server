# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/active_game_data/active_game_data_config.py

# Импорты реализаций репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.interfaces_active_game_data import IItemInstanceRepository, IUsedCharacterArchiveRepository
from .item_instance_repository_impl import ItemInstanceRepositoryImpl
from .used_character_archive_repository_impl import UsedCharacterArchiveRepositoryImpl # <--- ДОБАВЛЕНО


# Импорты интерфейсов



# Конфигурация для группы репозиториев 'active_game_data'
active_game_data_repo_config = [
    {
        "name": "item_instance_repository", # Уникальное имя репозитория для получения из инициализатора
        "implementation": ItemInstanceRepositoryImpl,
        "interface": IItemInstanceRepository
    },
    {
        "name": "used_character_archive_repository", # Уникальное имя для нового репозитория
        "implementation": UsedCharacterArchiveRepositoryImpl,
        "interface": IUsedCharacterArchiveRepository
    },
    # Если в будущем будут другие репозитории в этой группе (например, active_quest, npc_instance), добавьте их сюда.
]