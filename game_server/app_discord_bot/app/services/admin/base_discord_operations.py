# game_server/app_discord_bot/app/services/admin/base_discord_operations.py

import discord
import logging # <-- Добавлено для типизации
import inject # <-- Добавлено для inject.autoparams
from typing import Optional, Dict, Any, Union, List
from discord import Forbidden, Guild, CategoryChannel, HTTPException, Member, TextChannel, ForumChannel, VoiceChannel, ChannelType, utils, PermissionOverwrite, Role

# Импорт новой конфигурации каналов
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
# Импорт NameFormatter
from game_server.app_discord_bot.app.services.utils.name_formatter import NameFormatter




class BaseDiscordOperations:
    """
    Базовые операции для взаимодействия с Discord API.
    Содержит вспомогательные методы для поиска, создания и удаления
    Discord-сущностей (каналы, категории, роли).
    """
    # 🔥 ИЗМЕНЕНИЕ: Просто @inject.autoparams(), без строковых ключей.
    # Это позволит inject автоматически разрешать зависимости по их типам.
    @inject.autoparams()
    def __init__(self, bot: discord.Client, name_formatter: NameFormatter, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
        self.name_formatter = name_formatter


    async def get_guild_by_id(self, guild_id: int) -> Optional[Guild]:
        """Вспомогательный метод для получения объекта Guild по ID."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            try:
                guild = await self.bot.fetch_guild(guild_id)
            except (discord.NotFound, discord.HTTPException) as e:
                self.logger.error(f"Не удалось получить гильдию {guild_id}: {e}")
                return None
        return guild

    def get_discord_channel_type(self, type_str: str) -> ChannelType:
        """Вспомогательный метод для получения типа канала Discord из строки."""
        type_map = {
            "text": ChannelType.text,
            "voice": ChannelType.voice,
            "category": ChannelType.category,
            "news": ChannelType.text,
            "forum": ChannelType.text,
        }
        return type_map.get(type_str.lower(), ChannelType.text)

    async def create_discord_category(
        self, guild: Guild, category_name: str, 
        overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = None
    ) -> CategoryChannel:
        """
        Создает новую категорию в Discord.
        🔥 ИЗМЕНЕНИЕ: Принимает готовый словарь 'overwrites' для установки прав.
        """
        formatted_category_name = self.name_formatter.format_name_for_discord(category_name, 'category')
        
        existing_category = utils.get(guild.categories, name=formatted_category_name)
        if existing_category:
            self.logger.info(f"Категория '{formatted_category_name}' уже существует. Используем существующую.")
            return existing_category

        try:
            # 🔥 ИЗМЕНЕНИЕ: Передаем 'overwrites' напрямую.
            category_channel = await guild.create_category(name=formatted_category_name, overwrites=overwrites)
            self.logger.success(f"Создана категория: '{formatted_category_name}' (ID: {category_channel.id}).")
            return category_channel
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Ошибка Discord API при создании категории '{formatted_category_name}': {e}", exc_info=True)
            raise

    async def create_discord_channel(
        self, guild: Guild, channel_name: str, channel_type_str: str,
        parent_category: Optional[CategoryChannel] = None, 
        overwrites: Optional[Dict[Union[Role, Member], PermissionOverwrite]] = None,
        description: Optional[str] = None
    ) -> Optional[Union[TextChannel, VoiceChannel, ForumChannel]]:
        """
        Создает новый канал в Discord.
        🔥 ИЗМЕНЕНИЕ: Принимает готовый словарь 'overwrites' вместо простого словаря прав.
        Параметр 'private_for_member' удален в пользу более гибкого 'overwrites'.
        """
        discord_channel_type = self.get_discord_channel_type(channel_type_str)
        
        formatted_channel_name_for_lookup = self.name_formatter.format_name_for_discord(channel_name, discord_channel_type.name)
        clean_name_for_api = self.name_formatter.normalize_name_from_discord(channel_name, discord_channel_type.name)
        
        if not clean_name_for_api:
            self.logger.error(f"Имя канала '{channel_name}' после нормализации для Discord API стало пустым. Пропуск создания.")
            return None

        existing_channel = utils.get(guild.channels, name=formatted_channel_name_for_lookup.lstrip('#'), category=parent_category)

        if existing_channel and existing_channel.type == discord_channel_type:
            self.logger.info(f"Канал '{formatted_channel_name_for_lookup}' уже существует. Используем существующий.")
            return existing_channel

        # 🔥 ИЗМЕНЕНИЕ: 'overwrites' передаются напрямую.
        channel_kwargs_common = {
            "name": clean_name_for_api,
            "category": parent_category,
            "overwrites": overwrites or {}
        }
        if description: channel_kwargs_common["topic"] = description

        try:
            if discord_channel_type == ChannelType.voice:
                channel_obj = await guild.create_voice_channel(**channel_kwargs_common)
            elif discord_channel_type == ChannelType.text:
                channel_obj = await guild.create_text_channel(**channel_kwargs_common)
            else:
                self.logger.error(f"Попытка создать неподдерживаемый тип канала через create_discord_channel: {discord_channel_type.name}. Ожидается text или voice.")
                return None

            self.logger.success(f"Создан канал: '{formatted_channel_name_for_lookup}' (ID: {channel_obj.id}, Тип: {channel_type_str}).")
            return channel_obj
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Ошибка Discord API при создании канала '{formatted_channel_name_for_lookup}': {e}", exc_info=True)
            raise
            
    async def create_or_update_role(
        self, guild: discord.Guild, role_name: str,
        permissions_data: Optional[Dict[str, Any]] = None,
        color: Optional[discord.Color] = None,
        hoist: bool = False, mentionable: bool = False
    ) -> discord.Role:
        """
        Находит существующую роль по имени или создает новую с указанными параметрами.
        Принимает словарь permissions_data из конфига.
        """
        formatted_role_name = self.name_formatter.format_name_for_discord(role_name, 'role')

        existing_role = discord.utils.get(guild.roles, name=formatted_role_name)
        if existing_role:
            self.logger.info(f"Роль '{formatted_role_name}' уже существует. Используем существующую.")
            return existing_role
        
        discord_permissions = discord.Permissions.none()
        if permissions_data:
            for perm, value in permissions_data.items():
                if hasattr(discord.Permissions, perm):
                    setattr(discord_permissions, perm, value)
                else:
                    self.logger.warning(f"Неизвестное разрешение Discord: {perm}")
        
        try:
            new_role = await guild.create_role(
                name=formatted_role_name,
                permissions=discord_permissions,
                color=color or discord.Color.default(),
                hoist=hoist, mentionable=mentionable, reason="Создание роли по команде бота"
            )
            self.logger.success(f"Создана новая роль в Discord: '{new_role.name}' (ID: {new_role.id}).")
            return new_role
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Ошибка Discord API при создании роли '{formatted_role_name}': {e}", exc_info=True)
            raise

    async def delete_discord_entity(self, entity: Union[Role, CategoryChannel, TextChannel, VoiceChannel, ForumChannel]):
        """Универсально удаляет сущность Discord (роль, канал, категорию)."""
        try:
            entity_name = entity.name
            await entity.delete(reason="Удаление по команде бота.")
            self.logger.info(f"Сущность '{entity_name}' (ID: {entity.id}) успешно удалена из Discord.")
        except discord.NotFound:
            self.logger.warning(f"Сущность '{entity_name}' (ID: {entity.id}) не найдена, возможно уже удалена.")
        except Forbidden:
            self.logger.error(f"Нет прав на удаление сущности '{entity_name}'.")
            raise
        except HTTPException as e:
            self.logger.error(f"Ошибка Discord API при удалении сущности '{entity_name}': {e}")
            raise

    async def get_discord_object_by_id(self, guild: Guild, discord_id: int) -> Optional[Union[Role, CategoryChannel, TextChannel, VoiceChannel, ForumChannel]]:
        """Пытается найти объект Discord по его ID (роль, канал или категорию)."""
        obj = guild.get_channel(discord_id) or guild.get_role(discord_id)
        if obj:
            return obj
        
        try:
            obj = await self.bot.fetch_channel(discord_id)
            return obj
        except (discord.NotFound, discord.HTTPException):
            pass

        try:
            all_roles = await guild.fetch_roles()
            obj = discord.utils.get(all_roles, id=discord_id)
            return obj
        except (discord.NotFound, discord.HTTPException):
            self.logger.warning(f"Не удалось найти сущность с ID {discord_id} ни как канал, ни как роль.")
        
        return None
            
    async def create_player_role(self, guild: discord.Guild, account_id: int) -> Optional[discord.Role]:
        """
        Создает на сервере новую роль для игрока с именем "Player-<account_id>".
        Если роль уже существует, возвращает ее.
        """
        role_name = f"Player-{account_id}"
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            self.logger.info(f"Роль '{role_name}' уже существует. Используем ее.")
            return existing_role

        try:
            new_role = await guild.create_role(name=role_name, reason=f"Создание роли для аккаунта {account_id}")
            self.logger.success(f"Создана роль '{role_name}' в гильдии '{guild.name}'.")
            return new_role
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Не удалось создать роль '{role_name}': {e}", exc_info=True)
            return None

    async def create_invite_link(
        self, channel: discord.TextChannel, max_age: int = 600, max_uses: int = 1, temporary: bool = True
    ) -> Optional[str]:
        """
        Создает одноразовую, временную ссылку-приглашение в указанный канал.
        """
        try:
            invite = await channel.create_invite(
                max_age=max_age, max_uses=max_uses, temporary=temporary,
                reason="Создание приглашения для нового игрока"
            )
            self.logger.info(f"Создана ссылка-приглашение для канала '{channel.name}': {invite.url}")
            return invite.url
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Не удалось создать приглашение для канала '{channel.name}': {e}", exc_info=True)
            return None

    async def send_dm_message(self, user: Union[Member, discord.User], message_content: str) -> bool:
        """
        Отправляет личное сообщение пользователю.
        """
        try:
            await user.send(message_content)
            self.logger.info(f"Отправлено личное сообщение пользователю {user.id} ({user.name}).")
            return True
        except (Forbidden, HTTPException) as e:
            self.logger.error(f"Не удалось отправить личное сообщение пользователю {user.id}: {e}")
            return False