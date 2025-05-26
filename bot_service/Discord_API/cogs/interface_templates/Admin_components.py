import os
import sys

from game_server.services.logging.logging_setup import logger

# Добавляем корень проекта в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import discord
from discord.ext import commands
from discord.ui import View

class AdminPanelView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot


    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="\u2696\ufe0f Создать мир", style=discord.ButtonStyle.primary, custom_id="admin_create_world")
    async def create_world(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("SetupWorld")
        if cog:
            await cog.setup_world(await self._fake_ctx(interaction))

    @discord.ui.button(label="\U0001f3ad Создать роли", style=discord.ButtonStyle.success, custom_id="admin_create_roles")
    async def create_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RoleManager")
        if cog:
            await cog.create_roles(await self._fake_ctx(interaction))

    @discord.ui.button(label="\U0001f5d1 Удалить роли", style=discord.ButtonStyle.danger, custom_id="admin_delete_roles")
    async def delete_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("RoleManager")
        if cog:
            await cog.delete_roles(await self._fake_ctx(interaction))

    @discord.ui.button(label="\ud83d\udd10 Применить права", style=discord.ButtonStyle.secondary, custom_id="admin_apply_permissions")
    async def apply_permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("PermissionsCog")
        if cog:
            await cog.apply_permissions(await self._fake_ctx(interaction))

    @discord.ui.button(label="\ud83d\udeaa Сделать приватным", style=discord.ButtonStyle.secondary, custom_id="admin_make_private")
    async def make_channels_private(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("PermissionsCog")
        if cog:
            await cog.make_channels_private(await self._fake_ctx(interaction))

    async def _fake_ctx(self, interaction: discord.Interaction):
        class FakeCtx:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.channel = interaction.channel
                self.author = interaction.user

                async def send(content=None, **kwargs):
                    try:
                        if not interaction.response.is_done():
                            await interaction.response.send_message(content=content, ephemeral=True, **kwargs)
                        else:
                            await interaction.followup.send(content=content, ephemeral=True, **kwargs)
                    except discord.NotFound:
                        logger.warning("⚠️ Невозможно отправить сообщение: interaction устарела")
    
                self.send = send

        return FakeCtx(interaction)
