# Discord_API/cogs/admin/world_setup_gogs.py

from discord.ext import commands

# Импортируем наш централизованный логгер
from game_server.config.logging.logging_setup import app_logger as logger
world_setup_logger = logger.getChild(__name__)

# Импортируем наш оркестратор сервисов Discord сущностей


# Импортируем BOT_PREFIX из настроек
from game_server.app_discord_bot.app.services.admin.discord_entity_service import DiscordEntityService
from game_server.app_discord_bot.config.discord_settings import BOT_PREFIX

class WorldSetupCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.discord_entity_service = DiscordEntityService(bot)
        world_setup_logger.info("WorldSetupCommands Cog инициализирован.")

    # --- Проверка прав (только для создателя сервера) ---
    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Глобальная проверка для всех команд в этом Cog'е:
        разрешает выполнять команды только создателю (владельцу) сервера.
        """
        if not ctx.guild:
            await ctx.send("Эту команду можно использовать только на сервере (гильдии).")
            return False
        
        if ctx.author.id != ctx.guild.owner_id:
            world_setup_logger.warning(f"Пользователь {ctx.author} (ID: {ctx.author.id}) попытался использовать админскую команду без прав на сервере {ctx.guild.name}.")
            await ctx.send("У вас нет прав для использования этой команды. Только создатель сервера может ее использовать.")
            return False
        return True

    # --- Команда: !setup-hub ---
    @commands.command(
        name="setup-hub",
        help="Полностью настраивает структуру публичного Хаб-сервера Discord.",
        usage=f"{BOT_PREFIX}setup-hub"
    )
    @commands.guild_only()
    async def setup_hub_command(self, ctx: commands.Context):
        world_setup_logger.info(f"Команда !setup-hub вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        message = await ctx.send("Начинаю настройку Хаб-сервера... Это может занять некоторое время.")

        try:
            result = await self.discord_entity_service.setup_hub_layout(ctx.guild.id)
            await message.edit(content=f"✅ Хаб-сервер успешно настроен!\nСообщение от бэкенда: {result.get('message')}")
            world_setup_logger.info(f"Хаб-сервер {ctx.guild.name} (ID: {ctx.guild.id}) успешно настроен.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка настройки Хаб-сервера: {e}")
            world_setup_logger.error(f"Ошибка ValueError при настройке Хаб-сервера {ctx.guild.name}: {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при настройке Хаб-сервера.")
            world_setup_logger.critical(f"Непредвиденная ошибка при настройке Хаб-сервера {ctx.guild.name}: {e}", exc_info=True)


    # --- Команда: !teardown-hub ---
    @commands.command(
        name="teardown-hub",
        help="Полностью удаляет все сущности Discord, связанные с текущим сервером (Хабом).",
        usage=f"{BOT_PREFIX}teardown-hub"
    )
    @commands.guild_only()
    async def teardown_hub_command(self, ctx: commands.Context):
        world_setup_logger.info(f"Команда !teardown-hub вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        message = await ctx.send("Начинаю удаление всех сущностей Хаб-сервера... Это может занять некоторое время.")

        try:
            result = await self.discord_entity_service.teardown_discord_layout(ctx.guild.id)
            await message.edit(content=f"✅ Все сущности Хаб-сервера успешно удалены!\nСообщение от бэкенда: {result.get('message')}")
            world_setup_logger.info(f"Все сущности Хаб-сервера {ctx.guild.name} (ID: {ctx.guild.id}) успешно удалены.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка удаления сущностей Хаб-сервера: {e}")
            world_setup_logger.error(f"Ошибка ValueError при удалении сущностей Хаб-сервера {ctx.guild.name}: {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при удалении сущностей Хаб-сервера.")
            world_setup_logger.critical(f"Непредвиденная ошибка при удалении сущностей Хаб-сервера {ctx.guild.name}: {e}", exc_info=True)


    # --- Команда: !setup-game-server ---
    @commands.command(
        name="setup-game-server",
        help="Настраивает минимальную структуру для игрового сервера Discord.",
        usage=f"{BOT_PREFIX}setup-game-server"
    )
    @commands.guild_only()
    async def setup_game_server_command(self, ctx: commands.Context):
        world_setup_logger.info(f"Команда !setup-game-server вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        message = await ctx.send("Начинаю настройку игрового сервера... Это может занять некоторое время.")

        try:
            result = await self.discord_entity_service.setup_game_server_layout(ctx.guild.id)
            await message.edit(content=f"✅ Игровой сервер успешно настроен!\nСообщение от бэкенда: {result.get('message')}")
            world_setup_logger.info(f"Игровой сервер {ctx.guild.name} (ID: {ctx.guild.id}) успешно настроен.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка настройки игрового сервера: {e}")
            world_setup_logger.error(f"Ошибка ValueError при настройке игрового сервера {ctx.guild.name}: {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при настройке игрового сервера.")
            world_setup_logger.critical(f"Непредвиденная ошибка при настройке игрового сервера {ctx.guild.name}: {e}", exc_info=True)


    # --- Команда: !teardown-game-server ---
    @commands.command(
        name="teardown-game-server",
        help="Полностью удаляет все сущности Discord, связанные с текущим игровым сервером.",
        usage=f"{BOT_PREFIX}teardown-game-server"
    )
    @commands.guild_only()
    async def teardown_game_server_command(self, ctx: commands.Context):
        world_setup_logger.info(f"Команда !teardown-game-server вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        message = await ctx.send("Начинаю удаление всех сущностей игрового сервера... Это может занять некоторое время.")

        try:
            result = await self.discord_entity_service.teardown_discord_layout(ctx.guild.id)
            await message.edit(content=f"✅ Все сущности игрового сервера успешно удалены!\nСообщение от бэкенда: {result.get('message')}")
            world_setup_logger.info(f"Все сущности игрового сервера {ctx.guild.name} (ID: {ctx.guild.id}) успешно удалены.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка удаления сущностей игрового сервера: {e}")
            world_setup_logger.error(f"Ошибка ValueError при удалении сущностей игрового сервера {ctx.guild.name}: {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при удалении сущностей игрового сервера.")
            world_setup_logger.critical(f"Непредвиденная ошибка при удалении сущностей игрового сервера {ctx.guild.name}: {e}", exc_info=True)


    # --- Команда: !add-article ---
    @commands.command(
        name="add-article",
        help="Добавляет новый канал-статью в категорию 'Библиотека Знаний'.",
        usage=f"{BOT_PREFIX}add-article <название_статьи_через_дефисы>"
    )
    @commands.guild_only()
    async def add_article_command(self, ctx: commands.Context, *, channel_name: str):
        world_setup_logger.info(f"Команда !add-article '{channel_name}' вызвана пользователем {ctx.author} на сервере {ctx.guild.name}.")
        
        message = await ctx.send(f"Пытаюсь добавить канал-статью '{channel_name}'...")

        formatted_channel_name = channel_name.lower().replace(' ', '-')

        try:
            result = await self.discord_entity_service.add_article_channel(ctx.guild.id, formatted_channel_name)
            await message.edit(content=f"✅ Канал-статья '{formatted_channel_name}' успешно создан!\nСообщение от бэкенда: {result.get('message')}")
            world_setup_logger.info(f"Канал-статья '{formatted_channel_name}' успешно создан для {ctx.guild.name}.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка при добавлении канала-статьи: {e}")
            world_setup_logger.error(f"Ошибка ValueError при добавлении канала-статьи '{formatted_channel_name}': {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при добавлении канала-статьи.")
            world_setup_logger.critical(f"Непредвиденная ошибка при добавлении канала-статьи '{formatted_channel_name}': {e}", exc_info=True)

    # --- НОВАЯ КОМАНДА: !sync-roles ---
    @commands.command(
        name="sync-roles",
        help="Синхронизирует роли Discord с конфигурацией State Entities.",
        usage=f"{BOT_PREFIX}sync-roles"
    )
    @commands.guild_only()
    async def sync_roles_command(self, ctx: commands.Context):
        world_setup_logger.info(f"Команда !sync-roles вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")

        message = await ctx.send("Начинаю синхронизацию ролей Discord... Это может занять некоторое время.")

        try:
            # 1. Вызываем метод сервиса и получаем структурированный словарь:
            sync_result_dict = await self.discord_entity_service.sync_discord_roles(ctx.guild.id)

            # 2. Извлекаем данные из словаря для форматирования:
            status_overall = sync_result_dict.get("status", "error")
            message_overall = sync_result_dict.get("message", "Неизвестное сообщение о синхронизации.")
            details = sync_result_dict.get("details", {})

            # ИСПРАВЛЕНИЕ: Используем правильные ключи для created_count и updated_count
            created_count = details.get("created_count", 0)
            updated_count = details.get("updated_count", 0)
            
            # ИСПРАВЛЕНИЕ: synced_count должен быть суммой созданных и обновленных
            synced_count = created_count + updated_count 
            
            errors_list = details.get("errors", [])

            # 3. Формируем человекочитаемое сообщение:
            formatted_response = f"**Синхронизация ролей завершена:** {message_overall}\n"
            formatted_response += f"**Всего ролей обработано:** {synced_count}\n"
            formatted_response += f"**Создано в БД:** {created_count}\n" # Изменено на "в БД"
            formatted_response += f"**Обновлено в БД:** {updated_count}\n" # Изменено на "в БД"

            if errors_list:
                formatted_response += f"**Ошибки:** {len(errors_list)} (см. логи бота для деталей)\n"
                formatted_response += "⚠️ Пожалуйста, проверьте логи бота для получения полной информации об ошибках."
            
            # 4. Отправляем форматированное сообщение в Discord:
            await message.edit(content=f"✅ {formatted_response}") # Исправлено: используем message.edit
            world_setup_logger.info(f"Синхронизация ролей для гильдии {ctx.guild.name} (ID: {ctx.guild.id}) завершена.")
        except ValueError as e:
            await message.edit(content=f"❌ Ошибка синхронизации ролей: {e}")
            world_setup_logger.error(f"Ошибка ValueError при синхронизации ролей на сервере {ctx.guild.name}: {e}")
        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при синхронизации ролей.")
            world_setup_logger.critical(f"Непредвиденная ошибка при синхронизации ролей на сервере {ctx.guild.name}: {e}", exc_info=True)

    # --- НОВАЯ КОМАНДА: !delete-roles ---
    @commands.command(
        name="delete-roles",
        help="Удаляет указанные Discord роли с сервера и из базы данных по их ID. Использование: !delete-roles <role_id_1> <role_id_2> ...",
        usage=f"{BOT_PREFIX}delete-roles <ID_роли_1> <ID_роли_2> ..."
    )
    @commands.guild_only()
    async def delete_roles_command(self, ctx: commands.Context, *role_ids: int):
        world_setup_logger.info(f"Команда !delete-roles {role_ids} вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        if not role_ids:
            await ctx.send("❌ Пожалуйста, укажите хотя бы один ID роли для удаления.")
            return

        message = await ctx.send(f"Начинаю удаление ролей Discord с ID: {', '.join(map(str, role_ids))}...")

        try:
            # ИСПРАВЛЕНИЕ 1: Вызываем правильный метод для удаления ролей
            delete_result_dict = await self.discord_entity_service.delete_discord_roles_batch(ctx.guild.id, list(role_ids))

            # ИСПРАВЛЕНИЕ 2: Форматируем ответ для удаления ролей
            status_overall = delete_result_dict.get("status", "error")
            message_overall = delete_result_dict.get("message", "Неизвестное сообщение об удалении.")
            details = delete_result_dict.get("details", {})

            deleted_from_discord = details.get("deleted_from_discord", 0)
            deleted_from_backend = details.get("deleted_from_backend", 0)
            errors_list = details.get("errors", [])

            formatted_response = f"**Удаление ролей завершено:** {message_overall}\n"
            formatted_response += f"**Удалено из Discord:** {deleted_from_discord}\n"
            formatted_response += f"**Удалено из БД:** {deleted_from_backend}\n"

            if errors_list:
                formatted_response += f"**Ошибки:** {len(errors_list)} (см. логи бота для деталей)\n"
                formatted_response += "⚠️ Пожалуйста, проверьте логи бота для получения полной информации об ошибках."
            
            await message.edit(content=f"✅ {formatted_response}")
            world_setup_logger.info(f"Удаление ролей для гильдии {ctx.guild.name} (ID: {ctx.guild.id}) завершено.")

        except Exception as e:
            await message.edit(content=f"❌ Произошла непредвиденная ошибка при удалении ролей.")
            world_setup_logger.critical(f"Непредвиденная ошибка при удалении ролей на сервере {ctx.guild.name}: {e}", exc_info=True)


# Функция для загрузки Cog'а в бота
async def setup(bot: commands.Bot):
    await bot.add_cog(WorldSetupCommands(bot))
    world_setup_logger.info("WorldSetupCommands Cog загружен.")
