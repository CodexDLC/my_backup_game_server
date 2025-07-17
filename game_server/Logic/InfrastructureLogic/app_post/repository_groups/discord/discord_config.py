# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_config.py

# Импорты реализаций репозиториев
from .discord_entity_repository_impl import DiscordEntityRepositoryImpl


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository


# Конфигурация для группы репозиториев 'discord'
discord_repo_config = [
    {
        "name": "discord_entity_repository",
        "implementation": DiscordEntityRepositoryImpl,
        "interface": IDiscordEntityRepository
    },

]