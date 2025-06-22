# Discord_API/core/services/admin/base_discord_operations.py

import logging
from typing import Dict, Any, List, Optional, Union
import discord
from discord import Forbidden, Guild, CategoryChannel, HTTPException, TextChannel, ForumChannel, VoiceChannel, ChannelType, utils, PermissionOverwrite

from Discord_API.config.logging.logging_setup_discod import logger
base_ops_logger = logger.getChild(__name__)


class BaseDiscordOperations:
    """
    Базовые операции для взаимодействия с Discord API.
    Содержит вспомогательные методы для поиска, создания и удаления
    Discord-сущностей.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot

    async def get_guild_by_id(self, guild_id: int) -> Optional[Guild]:
        """Вспомогательный метод для получения объекта Guild по ID."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            try:
                guild = await self.bot.fetch_guild(guild_id)
                base_ops_logger.info(f"Гильдия {guild_id} найдена через fetch_guild.")
            except discord.NotFound:
                base_ops_logger.error(f"Гильдия с ID {guild_id} не найдена.")
                return None
            except discord.HTTPException as e:
                base_ops_logger.error(f"Ошибка HTTP при получении гильдии {guild_id}: {e}")
                return None
        return guild

    def get_discord_channel_type(self, type_str: str) -> ChannelType:
        """Вспомогательный метод для получения типа канала Discord из строки."""
        type_map = {
            "text": ChannelType.text,
            "voice": ChannelType.voice,
            "category": ChannelType.category,
            "news": ChannelType.news,
            "forum": ChannelType.forum,
        }
        return type_map.get(type_str.lower(), ChannelType.text)


    async def create_discord_category(self, guild: Guild, category_name: str, permissions: Optional[str] = None) -> CategoryChannel:
        """
        Создает новую категорию в Discord. Проверяет наличие перед созданием.
        Возвращает существующую или новую категорию.
        """
        existing_category = utils.get(guild.categories, name=category_name)
        if existing_category:
            base_ops_logger.info(f"Категория '{category_name}' уже существует в гильдии '{guild.name}'. Используем существующую.")
            return existing_category
        
        overwrites = {}
        default_role = guild.default_role

        # По умолчанию скрываем все от @everyone для категорий,
        # если явно не указан "public_view".
        overwrites[default_role] = discord.PermissionOverwrite(
            view_channel=False,
            read_messages=False,
            send_messages=False,
            connect=False,
            speak=False,
            manage_channels=False,
            manage_roles=False,
            manage_webhooks=False,
            create_instant_invite=False,
        )

        if permissions == "public_view": # Категория должна быть видна всем
            overwrites[default_role] = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=False
            )

        try:
            category_channel = await guild.create_category(name=category_name, overwrites=overwrites if overwrites else None)
            base_ops_logger.info(f"Создана категория: '{category_name}' (ID: {category_channel.id}) в гильдии '{guild.name}'.")
            return category_channel
        except discord.Forbidden:
            base_ops_logger.error(f"Бот не имеет прав для создания категории '{category_name}' в гильдии '{guild.name}'.")
            raise
        except discord.HTTPException as e:
            base_ops_logger.error(f"Ошибка Discord API при создании категории '{category_name}': {e}")
            raise
        except Exception as e:
            base_ops_logger.error(f"Непредвиденная ошибка при создании категории '{category_name}': {e}", exc_info=True)
            raise

    async def create_discord_channel(
        self,
        guild: Guild,
        channel_name: str,
        channel_type_str: str,
        parent_category: Optional[CategoryChannel] = None,
        permissions: Optional[str] = None, # "read_only", "admin_only", "moderator_only", "public", "player_chat", "tester_chat"
        description: Optional[str] = None,
        private_for_member: Optional[discord.Member] = None 
    ) -> Union[TextChannel, VoiceChannel, ForumChannel, None]:
        """
        Создает новый канал в Discord. Проверяет наличие перед созданием.
        Возвращает существующий или новый канал.
        Если указан private_for_member, создает приватный канал только для этого пользователя и @everyone будет запрещен.
        """
        discord_channel_type = self.get_discord_channel_type(channel_type_str)
        
        if parent_category:
            existing_channel = utils.get(parent_category.channels, name=channel_name.lstrip('#'))
        else:
            existing_channel = utils.get(guild.channels, name=channel_name.lstrip('#'))

        if existing_channel and existing_channel.type == discord_channel_type:
            base_ops_logger.info(f"Канал '{channel_name}' ({channel_type_str}) уже существует. Используем существующий.")
            return existing_channel

        channel_kwargs = {
            "name": channel_name.lstrip('#'),
            "category": parent_category
        }

        overwrites = {}
        default_role = guild.default_role

        # Всегда явно запрещаем @everyone ВСЁ по умолчанию на уровне канала,
        # а затем явно разрешаем только то, что нужно.
        # Это обеспечивает максимальный контроль над наследованием.
        overwrites[default_role] = discord.PermissionOverwrite(
            view_channel=False,
            read_messages=False,
            send_messages=False,
            connect=False,       
            speak=False,
            manage_channels=False,
            manage_roles=False,
            manage_webhooks=False,
            create_instant_invite=False,
            send_tts_messages=False,
            embed_links=False,
            attach_files=False,
            add_reactions=False,
            use_external_emojis=False,
            use_external_stickers=False,
            mention_everyone=False,
            manage_messages=False,
            read_message_history=False
        )

        if private_for_member:
            overwrites[default_role].update(view_channel=False)
            overwrites[private_for_member] = discord.PermissionOverwrite(
                view_channel=True,
                read_messages=True,
                send_messages=True
            )
        elif permissions == 'public':
            overwrites[default_role].update(
                view_channel=True,
                read_messages=True,
                send_messages=True
            )
            if discord_channel_type == ChannelType.news:
                 overwrites[default_role].update(
                    view_channel=True,
                    read_messages=True,
                    send_messages=False
                 )

        elif permissions == 'read_only':
            overwrites[default_role].update(
                view_channel=True,
                read_messages=True,
                send_messages=False
            )
        elif permissions == 'admin_only':
            admin_role = discord.utils.get(guild.roles, name="Администратор")
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, connect=True, speak=True)
            else:
                base_ops_logger.warning(f"Роль 'Администратор' не найдена для канала '{channel_name}'. Канал может быть не скрыт должным образом.")
        elif permissions == 'moderator_only':
            moderator_role = discord.utils.get(guild.roles, name="Модератор")
            if moderator_role:
                # Права модератора (из прошлого обсуждения)
                overwrites[moderator_role] = discord.PermissionOverwrite(
                    view_channel=True, read_messages=True, send_messages=True, # Базовые права
                    manage_messages=True, # Управление сообщениями
                    kick_members=True, ban_members=True, # Кик/бан
                    manage_nicknames=True, # Управление никнеймами
                    move_members=True, mute_members=True, deafen_members=True, # Управление в ГК
                    view_audit_log=True, # Просмотр журнала аудита
                    manage_webhooks=True, # Управление вебхуками
                    add_reactions=True, embed_links=True, attach_files=True,
                    use_external_emojis=True, use_external_stickers=True,
                    mention_everyone=True, # Упоминание всех (для объявлений)
                    # Остальные права - по умолчанию False (запрещены)
                )
            else:
                base_ops_logger.warning(f"Роль 'Модератор' не найдена для канала '{channel_name}'. Канал может быть не скрыт должным образом.")
        
        # --- НОВЫЙ БЛОК: Права для Игрока/Тестера ---
        elif permissions == 'player_chat':
            player_role = discord.utils.get(guild.roles, name="Игрок")
            if player_role:
                # Права Игрока
                overwrites[player_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    read_messages=True,
                    send_messages=True,
                    add_reactions=True,
                    embed_links=True,
                    attach_files=True,
                    use_external_emojis=True,
                    use_external_stickers=True,
                    read_message_history=True,
                    # Остальные права по умолчанию False (запрещены)
                )
            else:
                base_ops_logger.warning(f"Роль 'Игрок' не найдена для канала '{channel_name}'. Права могут быть не установлены.")
        elif permissions == 'tester_chat':
            tester_role = discord.utils.get(guild.roles, name="Тестер")
            if tester_role:
                # Права Тестера (такие же, как у Игрока, если нет специфических дополнений)
                overwrites[tester_role] = discord.PermissionOverwrite(
                    view_channel=True,
                    read_messages=True,
                    send_messages=True,
                    add_reactions=True,
                    embed_links=True,
                    attach_files=True,
                    use_external_emojis=True,
                    use_external_stickers=True,
                    read_message_history=True,
                    # Остальные права по умолчанию False (запрещены)
                )
            else:
                base_ops_logger.warning(f"Роль 'Тестер' не найдена для канала '{channel_name}'. Права могут быть не установлены.")
        # --- КОНЕЦ НОВОГО БЛОКА ---


        if overwrites:
            channel_kwargs["overwrites"] = overwrites

        # Настройка топика/описания
        if description and discord_channel_type in [ChannelType.text, ChannelType.news, ChannelType.forum]:
            channel_kwargs["topic"] = description

        try:
            channel_obj: Union[TextChannel, VoiceChannel, ForumChannel, None] = None
            if discord_channel_type == ChannelType.text:
                channel_obj = await guild.create_text_channel(**channel_kwargs)
            elif discord_channel_type == ChannelType.news:
                channel_obj = await guild.create_text_channel(**channel_kwargs)
                if hasattr(channel_obj, 'edit') and hasattr(channel_obj, 'type') and channel_obj.type == ChannelType.text:
                     try:
                         await channel_obj.edit(type=ChannelType.news)
                         base_ops_logger.info(f"Канал '{channel_name}' конвертирован в новостной канал.")
                     except Exception as convert_e:
                         base_ops_logger.warning(f"Не удалось конвертировать канал '{channel_name}' в новостной: {convert_e}")
                
            elif discord_channel_type == ChannelType.forum:
                temp_category = channel_kwargs.pop("category", None)
                channel_obj = await guild.create_forum(**channel_kwargs)
                if temp_category:
                    await channel_obj.edit(category=temp_category)
            elif discord_channel_type == ChannelType.voice:
                channel_obj = await guild.create_voice_channel(**channel_kwargs)
            else:
                base_ops_logger.warning(f"Неизвестный или неподдерживаемый тип канала '{channel_type_str}' для '{channel_name}'. Пропускаем.")
                return None
            
            base_ops_logger.info(f"Создан канал: '{channel_name}' (ID: {channel_obj.id}, Тип: {channel_type_str}) "
                                 f"{f'в категории {parent_category.name}' if parent_category else ''}.")
            return channel_obj

        except discord.Forbidden:
            base_ops_logger.error(f"Бот не имеет прав для создания канала '{channel_name}' в гильдии '{guild.name}'.")
            raise
        except discord.HTTPException as e:
            base_ops_logger.error(f"Ошибка Discord API при создании канала '{channel_name}': {e}")
            raise
        except Exception as e:
            base_ops_logger.error(f"Непредвиденная ошибка при создании канала '{channel_name}': {e}", exc_info=True)
            raise

    async def delete_discord_entity(self, discord_obj: Union[CategoryChannel, TextChannel, VoiceChannel, ForumChannel]) -> bool:
        """
        Удаляет сущность Discord (канал или категорию).
        """
        try:
            await discord_obj.delete(reason="Удаление по команде бота.")
            base_ops_logger.info(f"Удалена сущность из Discord: '{discord_obj.name}' (ID: {discord_obj.id}, Тип: {discord_obj.type}).")
            return True
        except discord.NotFound:
            base_ops_logger.warning(f"Сущность Discord '{discord_obj.name}' (ID: {discord_obj.id}) не найдена в Discord (возможно, уже удалена).")
            return False
        except discord.Forbidden:
            base_ops_logger.error(f"Бот не имеет прав на удаление сущности '{discord_obj.name}' (ID: {discord_obj.id}).")
            raise
        except discord.HTTPException as e:
            base_ops_logger.error(f"Ошибка Discord API при удалении сущности '{discord_obj.name}' (ID: {discord_obj.id}): {e}", exc_info=True)
            raise
        except Exception as e:
            base_ops_logger.error(f"Непредвиденная ошибка при удалении сущности '{discord_obj.name}' (ID: {discord_obj.id}): {e}", exc_info=True)
            raise

    async def get_discord_object_by_id(self, guild: Guild, discord_id: int) -> Optional[Union[CategoryChannel, TextChannel, VoiceChannel, ForumChannel]]:
        """
        Пытается найти объект Discord по его ID (канал или категорию).
        """
        obj = guild.get_channel(discord_id)
        if obj:
            return obj
        
        for category in guild.categories:
            if category.id == discord_id:
                return category
        
        try:
            fetched_obj = await self.bot.fetch_channel(discord_id)
            if isinstance(fetched_obj, (CategoryChannel, TextChannel, VoiceChannel, ForumChannel)):
                return fetched_obj
        except discord.NotFound:
            base_ops_logger.debug(f"Объект Discord с ID {discord_id} не найден через fetch_channel.")
            pass
        except discord.HTTPException as e:
            base_ops_logger.warning(f"Ошибка HTTP при fetch_channel для ID {discord_id}: {e}")

        return None
    
    async def set_channel_visibility_for_role_or_member(
        self,
        channel: Union[TextChannel, VoiceChannel, ForumChannel],
        target_role_or_member: Union[discord.Role, discord.Member],
        view_channel: Optional[bool] = None,
        send_messages: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Устанавливает или изменяет разрешения view_channel и send_messages для канала
        для указанной роли или пользователя.
        view_channel: True - разрешить, False - запретить, None - оставить наследуемым.
        send_messages: True - разрешить, False - запретить, None - оставить наследуемым.
        """
        overwrites = channel.overwrites_for(target_role_or_member)
        
        if view_channel is not None:
            overwrites.view_channel = view_channel
        if send_messages is not None:
            overwrites.send_messages = send_messages
        
        try:
            await channel.set_permissions(target_role_or_member, overwrite=overwrites)
            logger.info(f"Разрешения для '{target_role_or_member.name}' на канале '{channel.name}' обновлены (view_channel={view_channel}, send_messages={send_messages}).")
            return {"status": "success", "message": "Разрешения канала успешно обновлены."}
        except Forbidden as e:
            logger.error(f"Бот не имеет прав для изменения разрешений на канале '{channel.name}': {e}", exc_info=True)
            raise
        except HTTPException as e:
            logger.error(f"Ошибка Discord API при изменении разрешений на канале '{channel.name}': {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при изменении разрешений на канале '{channel.name}': {e}", exc_info=True)
            raise
