import discord
from discord.ext import commands

from game_server.app_discord_bot.app.ui.inventory_view import GameItem, PaginatedInventoryView


# app_commands больше не нужен для этой команды
# from discord import app_commands

# Импортируем наш новый View и класс предмета


# Создадим моковые (тестовые) данные для демонстрации
def get_mock_player_items() -> list[GameItem]:
    items = []
    for i in range(1, 31): # Создаем 30 предметов
        items.append(
            GameItem(
                item_id=f"item_{i}",
                name=f"Предмет #{i}",
                description=f"Очень полезная вещь номер {i}.",
                quantity=1
            )
        )
    return items

class InventoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
    @commands.command(name="inventory", help="Показывает ваш инвентарь.")
    async def inventory(self, ctx: commands.Context):
        """
        Показывает инвентарь игрока с пагинацией.
        """
        # В реальном приложении здесь будет вызов вашего API для получения предметов
        # player_items = await services.api_client.get_inventory(ctx.author.id)
        player_items = get_mock_player_items()

        if not player_items:
            await ctx.send("Ваш инвентарь пуст.")
            return
            
        # Создаем и отправляем наш View
        view = PaginatedInventoryView(items=player_items, author=ctx.author)
        # Отвечаем через ctx.send. ephemeral здесь не поддерживается,
        # поэтому сообщение будет видно всем.
        await ctx.send(embed=view._create_embed(), view=view)


async def setup(bot: commands.Bot):
    """Функция для загрузки кога в бота."""
    await bot.add_cog(InventoryCog(bot))
