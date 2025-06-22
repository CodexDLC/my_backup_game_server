# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/npc/npc_config.py

# Импорты реализаций репозиториев



# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.npc.monster.interfaces_monster import IEliteMonsterRepository
from .monster.elite_monster_repository_impl import EliteMonsterRepositoryImpl



# Конфигурация для группы репозиториев 'npc'
npc_repo_config = [
    {
        "name": "elite_monster_repository",
        "implementation": EliteMonsterRepositoryImpl,
        "interface": IEliteMonsterRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]