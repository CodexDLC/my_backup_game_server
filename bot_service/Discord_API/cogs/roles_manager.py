import os
import sys

# Добавляем корень проекта в sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from game_server.services.logging.logging_setup import logger
from discord.ext import commands

from bot_service.Discord_API.api.roles import *
from bot_service.Discord_API.discord_functions.roles_functions import create_roles_in_discord, delete_roles_from_discord



class RoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cr", help="Создаёт новые роли в Discord и записывает их в базу.")
    @commands.has_permissions(administrator=True)
    async def create_roles(self, ctx):
        await ctx.send("🔄 Начинаем создание ролей...")
        guild_id = ctx.guild.id  
        world_id = await get_world_id()
        if not world_id:
            await ctx.send("ERROR Ошибка: не удалось получить ID мира!")
            return

        existing_roles = await get_existing_roles(guild_id)
        available_flags = await get_available_flags()

        # 🔹 Формируем список новых ролей (без дублей)
        roles_to_create = [
            {"role_name": flag["code_name"], "access_code": flag["access_code"], "world_id": world_id}
            for flag in available_flags if flag["access_code"] not in existing_roles
        ]

        if not roles_to_create:
            await ctx.send("INFO Все роли уже существуют, создание не требуется!")
            return

        # 🔹 Создаём роли в Discord
        created_roles = await create_roles_in_discord(guild_id, self.bot, roles_to_create)

        # 🔹 Записываем роли в базу
        await save_roles_to_db(guild_id, world_id, created_roles)

        await ctx.send(f"INFO Создано {len(created_roles)} новых ролей в мире (ID: {world_id})!")






    @commands.command(name="list_roles")
    @commands.has_permissions(administrator=True)  # Только для администраторов
    async def list_roles(self, ctx):
        guild_id = ctx.guild.id  # Получаем ID сервера

        logger.info(f"🔄 Запущена команда `!list_roles` для сервера ID: {guild_id}")

        # INFO Запрашиваем существующие роли из базы API
        existing_roles = await get_existing_roles(guild_id)
        if not existing_roles:
            await ctx.send("📭 В базе нет сохранённых ролей!")
            logger.info("📭 Команда `!list_roles`: ролей не найдено.")
            return

        # 🔹 Формируем удобное отображение списка ролей
        role_list = "\n".join([f"🔹 `{role}`" for role in existing_roles])

        logger.info(f"📊 Список ролей в базе ({len(existing_roles)}):\n{role_list}")
        await ctx.send(f"📊 **Список ролей в базе ({len(existing_roles)}):**\n{role_list}")


    @commands.command(name="del_roles")
    @commands.has_permissions(administrator=True)
    async def delete_roles(self, ctx):
        """Удаляет все роли (кроме администраторов и системных) из Discord и базы."""
        guild_id = ctx.guild.id

        logger.info(f"🗑 Запущена команда `!del_roles` для сервера ID: {guild_id}")

        # INFO Вызываем функцию удаления ролей в Discord
        deleted_count = await delete_roles_from_discord(guild_id, self.bot)

        # INFO Удаляем роли из базы через API
        api_response = await delete_all_roles_from_db(guild_id)

        if api_response.get("status") == "success":
            logger.info("INFO Все роли успешно удалены из базы.")
        else:
            logger.error(f"ERROR Ошибка при удалении ролей из базы: {api_response.get('message')}")

        # INFO Запрашиваем обновлённый список ролей
        remaining_roles = await get_existing_roles(guild_id)
        if not remaining_roles:
            await ctx.send(f"INFO Удалено {deleted_count} ролей. Все роли успешно удалены!")
        else:
            await ctx.send(f"⚠️ В базе остались роли: {remaining_roles}")
            logger.warning(f"⚠️ Не все роли были удалены: {remaining_roles}")
            
# 🔧 Добавляем команду к боту
async def setup(bot):
    await bot.add_cog(RoleManager(bot))
