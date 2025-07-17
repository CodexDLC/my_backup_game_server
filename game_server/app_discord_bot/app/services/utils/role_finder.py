# app/services/utils/role_finder.py
import discord
import inject
from discord.ext import commands
from typing import Optional

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

class RoleFinder:
    """
    Хелпер-класс для инкапсуляции логики поиска системных ролей.
    """
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        guild_config_manager: IGuildConfigManager
    ):
        self.bot = bot
        self.guild_config_manager = guild_config_manager

    async def get_system_role(self, guild: discord.Guild, role_key: str, shard_type: str = "game") -> Optional[discord.Role]:
        """
        Находит и возвращает объект системной роли по ее ключу (например, OFFLINE_ROLE).
        """
        logger.debug(f"RoleFinder: Поиск системной роли с ключом '{role_key}' на сервере {guild.id}")
        
        system_roles_config = await self.guild_config_manager.get_field(
            guild_id=guild.id, 
            shard_type=shard_type, 
            field_name=RedisKeys.FIELD_SYSTEM_ROLES
        )
        if not system_roles_config:
            logger.error(f"Конфигурация системных ролей ('{RedisKeys.FIELD_SYSTEM_ROLES}') не найдена для шарда {guild.id}")
            return None

        # ▼▼▼ ИСПРАВЛЕНИЕ: Получаем словарь с данными о роли ▼▼▼
        role_data = system_roles_config.get(role_key)
        if not role_data or not isinstance(role_data, dict):
            logger.error(f"Данные для роли с ключом '{role_key}' не найдены или имеют неверный формат.")
            return None

        # ▼▼▼ ИСПРАВЛЕНИЕ: Извлекаем ID из словаря ▼▼▼
        role_id = role_data.get('discord_id')
        if not role_id:
            logger.error(f"Ключ 'id' не найден в данных для роли '{role_key}'.")
            return None

        # Теперь используем чистый ID для поиска
        role = guild.get_role(role_id)
        if not role:
            logger.warning(f"Роль {role_id} не найдена в кэше, пробую получить через API.")
            try:
                role = await guild.fetch_role(role_id)
            except discord.NotFound:
                logger.error(f"Роль с ID {role_id} не найдена на сервере {guild.id} даже через API.")
                return None
        
        logger.debug(f"RoleFinder: Роль '{role.name}' (ID: {role.id}) успешно найдена.")
        return role
