# game_server/app_discord_bot/app/services/utils/role_verification_service.py
import discord
import logging
from typing import Optional
import inject

from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

# Импортируем константы с названиями ролей
from game_server.app_discord_bot.app.constant.roles_blueprint import (
    ADMIN_ROLE, MOD_ROLE, TESTER_ROLE, ONLINE_ROLE, OFFLINE_ROLE, PLAYER_ROLE
)

class RoleVerificationService:
    """
    Сервис для проверки наличия у пользователя определенных системных ролей.
    Использует кэшированные ID ролей для эффективности.
    """
    @inject.autoparams()
    def __init__(self, guild_config_manager: IGuildConfigManager, logger: logging.Logger):
        self.guild_config_manager = guild_config_manager
        self.logger = logger
        self.logger.info("✨ RoleVerificationService инициализирован.")

    async def _get_role_id_from_cache(self, guild_id: int, role_name: str) -> Optional[int]:
        """Вспомогательный метод для получения ID роли из кэша."""
        system_roles = await self.guild_config_manager.get_field(
            guild_id=guild_id,
            shard_type="game", # Предполагаем, что проверка ролей нужна в основном на игровых шардах
            field_name=RedisKeys.FIELD_SYSTEM_ROLES
        )
        if not system_roles or not isinstance(system_roles, dict):
            return None
        
        role_data = system_roles.get(role_name)
        return role_data.get("discord_id") if role_data else None

    async def _has_role_by_name(self, member: discord.Member, role_name: str) -> bool:
        """Проверяет наличие роли у пользователя по ее имени (через кэш)."""
        role_id = await self._get_role_id_from_cache(member.guild.id, role_name)
        if not role_id:
            self.logger.warning(f"Роль '{role_name}' не найдена в кэше для гильдии {member.guild.id}.")
            return False
        
        return any(role.id == role_id for role in member.roles)

    async def is_admin(self, member: discord.Member) -> bool:
        """Проверяет, является ли пользователь администратором."""
        return await self._has_role_by_name(member, ADMIN_ROLE)

    async def is_moderator(self, member: discord.Member) -> bool:
        """Проверяет, является ли пользователь модератором."""
        return await self._has_role_by_name(member, MOD_ROLE)
        
    async def is_tester(self, member: discord.Member) -> bool:
        """Проверяет, является ли пользователь тестером."""
        return await self._has_role_by_name(member, TESTER_ROLE)

    async def is_player(self, member: discord.Member) -> bool:
        """Проверяет, есть ли у пользователя роль 'Игрок'."""
        return await self._has_role_by_name(member, PLAYER_ROLE)

    async def is_online(self, member: discord.Member) -> bool:
        """Проверяет, есть ли у пользователя роль 'Online player status'."""
        return await self._has_role_by_name(member, ONLINE_ROLE)

    async def is_offline(self, member: discord.Member) -> bool:
        """Проверяет, есть ли у пользователя роль 'Offline player status'."""
        return await self._has_role_by_name(member, OFFLINE_ROLE)