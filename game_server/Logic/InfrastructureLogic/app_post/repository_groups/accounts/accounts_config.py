# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/accounts_config.py

# Импорты реализаций репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository, IAccountInfoRepository
from .account_game_data_repository import AccountGameDataRepositoryImpl
from .account_info_repository_impl import AccountInfoRepositoryImpl # Убедитесь, что имя файла соответствует переименованию

# Импорты интерфейсов



# Конфигурация для группы репозиториев 'accounts'
accounts_repo_config = [
    {
        "name": "account_game_data_repository",
        "implementation": AccountGameDataRepositoryImpl,
        "interface": IAccountGameDataRepository
    },
    {
        "name": "account_info_repository",
        "implementation": AccountInfoRepositoryImpl,
        "interface": IAccountInfoRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]