# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/game_shards/game_shards_config.py

# Импорты реализаций репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from .game_shard_repository_impl import GameShardRepositoryImpl

# Импорты интерфейсов



# Конфигурация для группы репозиториев 'game_shards'
game_shards_repo_config = [
    {
        "name": "game_shard_repository", # Уникальное имя репозитория для получения из инициализатора
        "implementation": GameShardRepositoryImpl,
        "interface": IGameShardRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]