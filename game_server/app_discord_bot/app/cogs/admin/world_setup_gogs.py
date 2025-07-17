# game_server/app_discord_bot/app/cogs/admin/world_setup_gogs.py

import discord
from discord.ext import commands
import logging
import inject
from typing import Dict, Any, List, Optional
import asyncio

from game_server.app_discord_bot.app.constant.constants_world import HUB_GUILD_ID
from game_server.app_discord_bot.app.services.admin.discord_entity_service import DiscordEntityService
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager
from game_server.app_discord_bot.app.services.utils.name_formatter import NameFormatter
from game_server.app_discord_bot.config.discord_settings import BOT_PREFIX
from game_server.app_discord_bot.app.ui.messages.admin_command_messages import (
    COMMAND_STARTED, COMMAND_SUCCESS, COMMAND_ERROR_VALUE_ERROR,
    COMMAND_ERROR_UNEXPECTED, SETUP_HUB, TEARDOWN_HUB,
    SETUP_GAME_SERVER, TEARDOWN_GAME_SERVER,
    SYNC_ROLES, DELETE_ROLES, COMMAND_SKIPPED
)
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager

MESSAGE_TTL_SECONDS = 3600


class WorldSetupCommands(commands.Cog):
    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        logger: logging.Logger,
        discord_entity_service: DiscordEntityService,
        guild_config_manager: GuildConfigManager,
        cache_sync_manager: CacheSyncManager,
        name_formatter: NameFormatter,
    ):
        self.bot = bot
        self.logger = logger
        self.discord_entity_service = discord_entity_service
        self.guild_config_manager = guild_config_manager
        self.cache_sync_manager = cache_sync_manager
        self.name_formatter = name_formatter
        self.logger.info("✅ WorldSetupCommands (полностью DI-ready) инициализирован.")

    async def cog_check(self, ctx: commands.Context) -> bool:
        """
        Глобальная проверка для всех команд в этом Cog'е:
        разрешает выполнять команды только создателю (владельцу) сервера.
        """
        if not ctx.guild:
            await ctx.send("Эту команду можно использовать только на сервере (гильдии).")
            return False
        
        if ctx.author.id != ctx.guild.owner_id:
            self.logger.warning(f"Пользователь {ctx.author} (ID: {ctx.author.id}) попытался использовать админскую команду без прав на сервере {ctx.guild.name}.")
            await ctx.send("У вас нет прав для использования этой команды. Только создатель сервера может ее использовать.")
            return False
        return True

    async def _schedule_message_deletion(self, message: discord.Message, delay: int):
        """Вспомогательная функция для удаления сообщений"""
        try:
            await asyncio.sleep(delay)
            await message.delete()
            self.logger.debug(f"Сообщение {message.id} успешно удалено после {delay} секунд.")
        except discord.NotFound:
            self.logger.debug(f"Сообщение {message.id} уже было удалено.")
        except discord.Forbidden:
            self.logger.warning(f"У бота нет прав для удаления сообщения {message.id}.")
        except Exception as e:
            self.logger.error(f"Непредвиденная ошибка при удалении сообщения {message.id}: {e}", exc_info=True)


    # --- Команда: !setup-hub ---
    @commands.command(
        name="setup-hub",
        help="Полностью настраивает структуру публичного Хаб-сервера Discord.",
        usage=f"{BOT_PREFIX}setup-hub"
    )
    @commands.guild_only()
    async def setup_hub_command(self, ctx: commands.Context):
        self.logger.info(f"Команда !setup-hub вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        initial_embed = discord.Embed(
            title=SETUP_HUB["title"],
            description=COMMAND_STARTED.format(SETUP_HUB["action"]),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        try:
            result = await self.discord_entity_service.setup_hub_layout(ctx.guild.id)
            
            if result.get("status") == "success":
                final_embed = discord.Embed(
                    title=SETUP_HUB["title"],
                    description=COMMAND_SUCCESS.format(SETUP_HUB["action"].capitalize(), result.get('message', SETUP_HUB["success_description"])),
                    color=discord.Color.green()
                )
                self.logger.info(f"Хаб-сервер {ctx.guild.name} (ID: {ctx.guild.id}) успешно настроен.")
            else:
                final_embed = discord.Embed(
                    title=SETUP_HUB["title"],
                    description=COMMAND_ERROR_UNEXPECTED.format(SETUP_HUB["action"]),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=result.get('message', "Неизвестная ошибка."), inline=False)
                self.logger.error(f"Ошибка при настройке Хаб-сервера {ctx.guild.name}: {result.get('message')}")

            await initial_message.edit(embed=final_embed)
        
        except ValueError as e:
            error_embed = discord.Embed(
                title=SETUP_HUB["title"],
                description=COMMAND_ERROR_VALUE_ERROR.format(SETUP_HUB["action"], e),
                color=discord.Color.red()
            )
            await initial_message.edit(embed=error_embed)
            self.logger.error(f"Ошибка ValueError при настройке Хаб-сервера {ctx.guild.name}: {e}")
        except Exception as e:
            error_embed = discord.Embed(
                title=SETUP_HUB["title"],
                description=COMMAND_ERROR_UNEXPECTED.format(SETUP_HUB["action"]),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при настройке Хаб-сервера {ctx.guild.name}: {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))


    # --- Команда: !teardown-hub ---
    @commands.command(
        name="teardown-hub",
        help="Полностью удаляет все сущности Discord, связанные с текущим сервером (Хабом).",
        usage=f"{BOT_PREFIX}teardown-hub"
    )
    @commands.guild_only()
    async def teardown_hub_command(self, ctx: commands.Context):
        self.logger.info(f"Команда !teardown-hub вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        initial_embed = discord.Embed(
            title=TEARDOWN_HUB["title"],
            description=COMMAND_STARTED.format(TEARDOWN_HUB["action"]),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        try:
            result = await self.discord_entity_service.teardown_discord_layout(ctx.guild.id, "hub")
            
            if result.get("status") == "success":
                final_embed = discord.Embed(
                    title=TEARDOWN_HUB["title"],
                    description=COMMAND_SUCCESS.format(TEARDOWN_HUB["action"].capitalize(), result.get('message', TEARDOWN_HUB["success_description"])),
                    color=discord.Color.green()
                )
                self.logger.info(f"Все сущности Хаб-сервера {ctx.guild.name} (ID: {ctx.guild.id}) успешно удалены.")
            elif result.get("status") == "skipped":
                 final_embed = discord.Embed(
                    title=TEARDOWN_HUB["title"],
                    description=COMMAND_SKIPPED.format(TEARDOWN_HUB["action"].capitalize(), result.get('message', "Нет сущностей для удаления.")),
                    color=discord.Color.orange()
                )
            else:
                final_embed = discord.Embed(
                    title=TEARDOWN_HUB["title"],
                    description=COMMAND_ERROR_UNEXPECTED.format(TEARDOWN_HUB["action"]),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=result.get('message', "Неизвестная ошибка."), inline=False)
                self.logger.error(f"Ошибка при удалении сущностей Хаб-сервера {ctx.guild.name}: {result.get('message')}")

            await initial_message.edit(embed=final_embed)
        
        except ValueError as e:
            error_embed = discord.Embed(
                title=TEARDOWN_HUB["title"],
                description=COMMAND_ERROR_VALUE_ERROR.format(TEARDOWN_HUB["action"], e),
                color=discord.Color.red()
            )
            await initial_message.edit(embed=error_embed)
            self.logger.error(f"Ошибка ValueError при удалении сущностей Хаб-сервера {ctx.guild.name}: {e}")
        except Exception as e:
            error_embed = discord.Embed(
                title=TEARDOWN_HUB["title"],
                description=COMMAND_ERROR_UNEXPECTED.format(TEARDOWN_HUB["action"]),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при удалении сущностей Хаб-сервера {ctx.guild.name}: {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))


    # --- Команда: !setup-game-server ---
    @commands.command(
        name="setup-game-server",
        help="Настраивает минимальную структуру для игрового сервера Discord.",
        usage=f"{BOT_PREFIX}setup-game-server"
    )
    @commands.guild_only()
    async def setup_game_server_command(self, ctx: commands.Context):
        self.logger.info(f"Команда !setup-game-server вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        initial_embed = discord.Embed(
            title=SETUP_GAME_SERVER["title"],
            description=COMMAND_STARTED.format(SETUP_GAME_SERVER["action"]),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        try:
            result = await self.discord_entity_service.setup_game_server_layout(ctx.guild.id)
            
            if result.get("status") == "success":
                final_embed = discord.Embed(
                    title=SETUP_GAME_SERVER["title"],
                    description=COMMAND_SUCCESS.format(SETUP_GAME_SERVER["action"].capitalize(), result.get('message', SETUP_GAME_SERVER["success_description"])),
                    color=discord.Color.green()
                )
                self.logger.info(f"Игровой сервер {ctx.guild.name} (ID: {ctx.guild.id}) успешно настроен.")
            else:
                final_embed = discord.Embed(
                    title=SETUP_GAME_SERVER["title"],
                    description=COMMAND_ERROR_UNEXPECTED.format(SETUP_GAME_SERVER["action"]),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=result.get('message', "Неизвестная ошибка."), inline=False)
                self.logger.error(f"Ошибка при настройке игрового сервера {ctx.guild.name}: {result.get('message')}")

            await initial_message.edit(embed=final_embed)
        
        except ValueError as e:
            error_embed = discord.Embed(
                title=SETUP_GAME_SERVER["title"],
                description=COMMAND_ERROR_VALUE_ERROR.format(SETUP_GAME_SERVER["action"], e),
                color=discord.Color.red()
            )
            await initial_message.edit(embed=error_embed)
            self.logger.error(f"Ошибка ValueError при настройке игрового сервера {ctx.guild.name}: {e}")
        except Exception as e:
            error_embed = discord.Embed(
                title=SETUP_GAME_SERVER["title"],
                description=COMMAND_ERROR_UNEXPECTED.format(SETUP_GAME_SERVER["action"]),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при настройке игрового сервера {ctx.guild.name}: {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))


    # --- Команда: !teardown-game-server ---
    @commands.command(
        name="teardown-game-server",
        help="Полностью удаляет все сущности Discord, связанные с текущим игровым сервером.",
        usage=f"{BOT_PREFIX}teardown-game-server"
    )
    @commands.guild_only()
    async def teardown_game_server_command(self, ctx: commands.Context):
        self.logger.info(f"Команда !teardown-game-server вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        initial_embed = discord.Embed(
            title=TEARDOWN_GAME_SERVER["title"],
            description=COMMAND_STARTED.format(TEARDOWN_GAME_SERVER["action"]),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        try:
            result = await self.discord_entity_service.teardown_discord_layout(ctx.guild.id, "game")
            
            if result.get("status") == "success":
                final_embed = discord.Embed(
                    title=TEARDOWN_GAME_SERVER["title"],
                    description=COMMAND_SUCCESS.format(TEARDOWN_GAME_SERVER["action"].capitalize(), result.get('message', TEARDOWN_GAME_SERVER["success_description"])),
                    color=discord.Color.green()
                )
                self.logger.info(f"Все сущности игрового сервера {ctx.guild.name} (ID: {ctx.guild.id}) успешно удалены.")
            elif result.get("status") == "skipped":
                 final_embed = discord.Embed(
                    title=TEARDOWN_GAME_SERVER["title"],
                    description=COMMAND_SKIPPED.format(TEARDOWN_GAME_SERVER["action"].capitalize(), result.get('message', "Нет сущностей для удаления.")),
                    color=discord.Color.orange()
                )
            else:
                final_embed = discord.Embed(
                    title=TEARDOWN_GAME_SERVER["title"],
                    description=COMMAND_ERROR_UNEXPECTED.format(TEARDOWN_GAME_SERVER["action"]),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=result.get('message', "Неизвестная ошибка."), inline=False)
                self.logger.error(f"Ошибка при удалении сущностей игрового сервера {ctx.guild.name}: {result.get('message')}")

            await initial_message.edit(embed=final_embed)
        
        except ValueError as e:
            error_embed = discord.Embed(
                title=TEARDOWN_GAME_SERVER["title"],
                description=COMMAND_ERROR_VALUE_ERROR.format(TEARDOWN_GAME_SERVER["action"], e),
                color=discord.Color.red()
            )
            await initial_message.edit(embed=error_embed)
            self.logger.error(f"Ошибка ValueError при удалении сущностей игрового сервера {ctx.guild.name}: {e}")
        except Exception as e:
            error_embed = discord.Embed(
                title=TEARDOWN_GAME_SERVER["title"],
                description=COMMAND_ERROR_UNEXPECTED.format(TEARDOWN_GAME_SERVER["action"]),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при удалении сущностей игрового сервера {ctx.guild.name}: {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))


    # --- Команда: !add-article ---
    @commands.command(
        name="add-article",
        help="Добавляет новый канал-статью в категорию 'Библиотека Знаний'.",
        usage=f"{BOT_PREFIX}add-article <название_статьи_через_дефисы>"
    )
    @commands.guild_only()
    async def add_article_command(self, ctx: commands.Context, *, channel_name: str):
        self.logger.info(f"Команда !add-article '{channel_name}' вызвана пользователем {ctx.author} на сервере {ctx.guild.name}.")
        
        initial_embed = discord.Embed(
            title="Добавление статьи",
            description=COMMAND_STARTED.format(f"добавление канала-статьи '{channel_name}'"),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        formatted_channel_name = channel_name.lower().replace(' ', '-')

        try:
            result = await self.discord_entity_service.add_article_channel(ctx.guild.id, formatted_channel_name)
            
            if result.get("status") == "success":
                final_embed = discord.Embed(
                    title="Добавление статьи",
                    description=COMMAND_SUCCESS.format("Канал-статья", result.get('message', f"Канал-статья '{formatted_channel_name}' успешно создан!")),
                    color=discord.Color.green()
                )
                self.logger.info(f"Канал-статья '{formatted_channel_name}' успешно создан для {ctx.guild.name}.")
            else:
                final_embed = discord.Embed(
                    title="Добавление статьи",
                    description=COMMAND_ERROR_UNEXPECTED.format(f"добавление канала-статьи '{channel_name}'"),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=result.get('message', "Неизвестная ошибка."), inline=False)
                self.logger.error(f"Ошибка при добавлении канала-статьи '{formatted_channel_name}': {result.get('message')}")

            await initial_message.edit(embed=final_embed)
        
        except ValueError as e:
            error_embed = discord.Embed(
                title="Добавление статьи",
                description=COMMAND_ERROR_VALUE_ERROR.format(f"добавление канала-статьи '{channel_name}'", e),
                color=discord.Color.red()
            )
            await initial_message.edit(embed=error_embed)
            self.logger.error(f"Ошибка ValueError при добавлении канала-статьи '{formatted_channel_name}': {e}")
        except Exception as e:
            error_embed = discord.Embed(
                title="Добавление статьи",
                description=COMMAND_ERROR_UNEXPECTED.format(f"добавление канала-статьи '{channel_name}'"),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при добавлении канала-статьи '{formatted_channel_name}': {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))

    
    # 🔥 ИЗМЕНЕНИЕ: Команда !sync-roles удалена, так как ее логика стала частью setup-команд.
    

    # --- Команда: !delete-roles ---
    @commands.command(
        name="delete-roles",
        help="Удаляет указанные Discord роли с сервера и из базы данных по их ID. Использование: !delete-roles <role_id_1> <role_id_2> ...",
        usage=f"{BOT_PREFIX}delete-roles <ID_роли_1> <ID_роли_2> ..."
    )
    @commands.guild_only()
    async def delete_roles_command(self, ctx: commands.Context, *role_ids: int):
        self.logger.info(f"Команда !delete-roles {role_ids} вызвана пользователем {ctx.author} на сервере {ctx.guild.name} (ID: {ctx.guild.id}).")
        
        if not role_ids:
            error_embed = discord.Embed(
                title=DELETE_ROLES["title"],
                description="❌ Пожалуйста, укажите хотя бы один ID роли для удаления.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))
            return

        initial_embed = discord.Embed(
            title=DELETE_ROLES["title"],
            description=COMMAND_STARTED.format(f"удаление ролей Discord с ID: {', '.join(map(str, role_ids))}"),
            color=discord.Color.blue()
        )
        initial_message = await ctx.send(embed=initial_embed)

        try:
            delete_result_dict = await self.discord_entity_service.delete_discord_roles_batch(ctx.guild.id, list(role_ids))

            status_overall = delete_result_dict.get("status", "error")
            message_overall = delete_result_dict.get("message", "Неизвестное сообщение об удалении.")
            details = delete_result_dict.get("details", {})

            deleted_from_discord = details.get("deleted_from_discord", 0)
            deleted_from_backend = details.get("deleted_from_backend", 0)
            errors_list = details.get("errors", [])

            if status_overall == "success":
                formatted_response = DELETE_ROLES["base_success_message"].format(message_overall)
                formatted_response += DELETE_ROLES["details_format"].format(deleted_from_discord, deleted_from_backend)
                if errors_list:
                    formatted_response += DELETE_ROLES["errors_summary"].format(len(errors_list))
                
                final_embed = discord.Embed(
                    title=DELETE_ROLES["title"],
                    description=formatted_response,
                    color=discord.Color.green() if not errors_list else discord.Color.orange()
                )
                self.logger.info(f"Удаление ролей для гильдии {ctx.guild.name} (ID: {ctx.guild.id}) завершено.")
            else:
                final_embed = discord.Embed(
                    title=DELETE_ROLES["title"],
                    description=COMMAND_ERROR_UNEXPECTED.format(DELETE_ROLES["action"]),
                    color=discord.Color.red()
                )
                final_embed.add_field(name="Сообщение", value=message_overall, inline=False)
                self.logger.error(f"Ошибка при удалении ролей на сервере {ctx.guild.name}: {message_overall}")
            
            await initial_message.edit(embed=final_embed)

        except Exception as e:
            error_embed = discord.Embed(
                title=DELETE_ROLES["title"],
                description=COMMAND_ERROR_UNEXPECTED.format(DELETE_ROLES["action"]),
                color=discord.Color.red()
            )
            error_embed.add_field(name="Детали", value=f"```py\n{e}\n```", inline=False)
            await initial_message.edit(embed=error_embed)
            self.logger.critical(f"Непредвиденная ошибка при удалении ролей на сервере {ctx.guild.name}: {e}", exc_info=True)
        finally:
            asyncio.create_task(self._schedule_message_deletion(initial_message, MESSAGE_TTL_SECONDS))
            asyncio.create_task(self._schedule_message_deletion(ctx.message, MESSAGE_TTL_SECONDS))