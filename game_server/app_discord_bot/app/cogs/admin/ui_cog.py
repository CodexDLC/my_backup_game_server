import discord
from discord.ext import commands

from game_server.app_discord_bot.app.ui.views import FullUIPanel


# app_commands больше не нужен для этой команды
# from discord import app_commands 

# Важно: импортируем наш View из папки core/ui



class UIDemoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
    # 1. Заменяем декоратор на @commands.command
    @commands.command(
        name="show_ui_demo", 
        aliases=["ui_test"], 
        help="Показывает демонстрационную UI панель."
    )
    # 2. Используем стандартный декоратор прав для префиксных команд
    @commands.has_permissions(administrator=True) 
    async def show_ui_demo(
        self,
        ctx: commands.Context, # 3. Тип взаимодействия теперь commands.Context
        channel: discord.TextChannel = None
    ):
        """
        Отправляет сообщение с демонстрационной панелью UI компонентов.
        
        Parameters
        ----------
        channel: Канал, в который будет отправлена панель. Если не указан, используется текущий.
        """
        # Если канал не указан, используем тот, где была вызвана команда
        target_channel = channel or ctx.channel

        if not target_channel:
            # 4. Отвечаем через ctx.send
            await ctx.send("Не удалось определить канал для отправки.")
            return

        embed = discord.Embed(
            title="Демонстрация UI Компонентов",
            description="Ниже представлены все основные элементы интерфейса, доступные в `discord.py`.\n\n"
                        "Нажмите на любой элемент для взаимодействия.",
            color=discord.Color.blurple()
        )
        
        # Создаем экземпляр нашего View и прикрепляем его к сообщению
        view = FullUIPanel()
        
        try:
            await target_channel.send(embed=embed, view=view)
            # Уведомляем пользователя об успехе в канале, где была вызвана команда
            await ctx.message.add_reaction("✅") 
        except discord.Forbidden:
            await ctx.send(
                f"У меня нет прав на отправку сообщений в канал {target_channel.mention}."
            )
        except Exception as e:
            await ctx.send(f"Произошла непредвиденная ошибка: {e}")


async def setup(bot: commands.Bot):
    """Функция для загрузки кога в бота."""
    await bot.add_cog(UIDemoCog(bot))
