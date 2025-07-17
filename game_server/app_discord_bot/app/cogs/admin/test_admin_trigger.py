import inject
from discord.ext import commands

from game_server.app_discord_bot.app.ui.views.admin.test_green_view import TestGreenView


class TestAdminTrigger(commands.Cog):
    # 🔥 ИЗМЕНЕНИЕ: Добавляем декоратор, как в ваших рабочих когах.
    # Он скажет `inject` самостоятельно найти 'bot' в DI-контейнере.
    @inject.autoparams()
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="test_command")
    @commands.is_owner()
    async def test_command(self, ctx: commands.Context):
        await ctx.send("Состояние А (зеленое)", view=TestGreenView())

# Функция setup() не нужна, так как ваш cog_manager её не использует.
# async def setup(bot: commands.Bot):
#     ...