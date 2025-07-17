# game_server\app_discord_bot\app\services\authentication\lobby\logic_handlers\logout_lobby.py

import inject
import discord
from discord.ext import commands

from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.app.constant.roles_blueprint import OFFLINE_ROLE, ONLINE_ROLE
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys

class LogoutHandlerlobby:
    """
    Обработчик логики для выхода из лобби.
    Меняет роли и не требует визуального ответа.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: IAccountDataManager,
        role_finder: RoleFinder,
    ):
        self.account_data_manager = account_data_manager
        self.role_finder = role_finder

    async def execute(self, payload: str, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild
        print(f"[+] Logic Handler (logout): Выполняется смена ролей для {user.name}.")

        # 1. Получаем роли
        roles_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_ROLES)
        personal_role_id = int(roles_data["personal_role_id"])
        
        offline_role = await self.role_finder.get_system_role(guild, OFFLINE_ROLE, shard_type="game")
        online_role = await self.role_finder.get_system_role(guild, ONLINE_ROLE, shard_type="game")
        personal_role = guild.get_role(personal_role_id)

        # 2. Меняем роли
        if online_role: await user.remove_roles(online_role, reason="Выход из лобби")
        if personal_role: await user.remove_roles(personal_role, reason="Выход из лобби")
        if offline_role: await user.add_roles(offline_role, reason="Выход из лобби")
        
        # 3. Отправляем эфемерный ответ и завершаем
        await interaction.followup.send("Вы вышли из лобби.", ephemeral=True)
        
        # 🔥 ГЛАВНОЕ ИЗМЕНЕНИЕ: Возвращаем None, чтобы оркестратор остановился
        return None
