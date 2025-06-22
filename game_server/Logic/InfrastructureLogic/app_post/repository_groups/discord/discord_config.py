# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_config.py

# Импорты реализаций репозиториев
from .discord_entity_repository_impl import DiscordEntityRepositoryImpl
from .discord_roles_mapping_repository_impl import DiscordRolesMappingRepositoryImpl

# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository, IDiscordRolesMappingRepository


# Конфигурация для группы репозиториев 'discord'
discord_repo_config = [
    {
        "name": "discord_entity_repository",
        "implementation": DiscordEntityRepositoryImpl,
        "interface": IDiscordEntityRepository
    },
    {
        "name": "discord_roles_mapping_repository",
        "implementation": DiscordRolesMappingRepositoryImpl,
        "interface": IDiscordRolesMappingRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]