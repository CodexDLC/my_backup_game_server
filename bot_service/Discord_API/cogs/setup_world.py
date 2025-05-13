import os
import sys
import discord
from discord.ext import commands
import logging

# 🔧 Добавляем корень проекта в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from Discord_API.api.world import *


logger = logging.getLogger(__name__)

class SetupWorld(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setupw")
    @commands.has_permissions(administrator=True)
    async def setup_world(self, ctx: commands.Context):
        """Создает Discord-структуру для игрового мира."""
        # 1. Получаем world_id
        world_id = await get_world_id()
        if not world_id:
            await ctx.send("ERROR Ошибка: не удалось получить ID мира!")
            logger.error("ERROR Ошибка при получении `world_id`!")
            return

        await ctx.send(f"🔧 Начинаем создание структуры для мира (ID: {world_id})")
        logger.info(f"🔧 Запущено создание структуры мира с ID {world_id}")

        # 2. Запрашиваем все регионы из базы
        regions = await fetch_all_regions()  # Получаем все регионы, не фильтруя по world_id

        # 3. Получаем все привязки для текущего мира
        bindings = await fetch_bindings(ctx.guild.id)  # Привязки для гильдии в discord_bindings
        bindings_map = {b["entity_access_key"]: b for b in bindings}  # Привязываем по access_key

        # 4. Обрабатываем регионы
        for region in regions:
            # Проверяем, существует ли категория в Discord с именем региона
            category = discord.utils.get(ctx.guild.categories, name=region["name"])
            if not category:
                # Если нет, создаем новую категорию
                category = await ctx.guild.create_category(name=region["name"])
                logger.info(f"Создана категория для региона {region['name']}")

            await category.edit(overwrites={ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)})
            logger.info(f"Категория {category.name} приватизирована для всех")
            # 5. Сохраняем привязку региона в discord_bindings
            if region["access_key"] not in bindings_map:
                await save_binding(ctx.guild.id, world_id, region["access_key"], category.id, None)

            # 6. Получаем подрегионы для этого региона
            subregions = await fetch_all_subregions(region["access_key"])

            # 7. Обрабатываем подрегионы
            for sub in subregions:
                # Проверяем, существует ли канал для подрегиона в соответствующей категории
                channel = discord.utils.get(category.text_channels, name=sub["name"])
                if not channel:
                    # Если канала нет, создаем новый канал
                    channel = await category.create_text_channel(
                        name=sub["name"],
                        topic=sub.get("description")
                    )
                    logger.info(f"Создан канал для подрегиона {sub['name']}")
                # Устанавливаем канал как приватный для всех (включаем "Приватный канал")
                await channel.edit(private=True)  # Приватизируем канал

                # 8. Сохраняем привязку подрегиона в discord_bindings
                if sub["access_key"] not in bindings_map:
                    await save_binding(ctx.guild.id, world_id, sub["access_key"], None, channel.id)

        # 9. Завершаем процесс
        await ctx.send("INFO Мир успешно создан!")
        logger.info(f"INFO Структура мира для {world_id} успешно создана!")




async def setup(bot):
    await bot.add_cog(SetupWorld(bot))
