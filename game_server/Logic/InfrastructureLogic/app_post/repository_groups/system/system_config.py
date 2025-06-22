# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/system/system_config.py

# Импорты реализаций репозиториев
from .data_version_repository_impl import DataVersionRepositoryImpl


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository


# Конфигурация для группы репозиториев 'system'
system_repo_config = [
    {
        "name": "data_version_repository",
        "implementation": DataVersionRepositoryImpl,
        "interface": IDataVersionRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]