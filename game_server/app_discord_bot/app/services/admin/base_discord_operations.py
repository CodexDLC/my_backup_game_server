# app/services/admin/base_discord_operations.py
import discord
from typing import Optional, Dict, Any, Union, List
from discord import Forbidden, Guild, CategoryChannel, HTTPException, Member, TextChannel, ForumChannel, VoiceChannel, ChannelType, utils, PermissionOverwrite, Role
from game_server.config.logging.logging_setup import app_logger as logger
# Импорт новой конфигурации каналов
from game_server.app_discord_bot.config.assets.data.channels_config import CHANNELS_CONFIG
# Импорт NameFormatter
from game_server.app_discord_bot.app.services.utils.name_formatter import NameFormatter
import re


class BaseDiscordOperations:
    """
    Базовые операции для взаимодействия с Discord API.
    Содержит вспомогательные методы для поиска, создания и удаления
    Discord-сущностей (каналы, категории, роли).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        # Инициализация NameFormatter
        if "emojis_formatting" not in CHANNELS_CONFIG:
            logger.critical("Конфигурация 'emojis_formatting' не найдена в CHANNELS_CONFIG. NameFormatter не может быть инициализирован.")
            raise RuntimeError("Emojis formatting configuration is missing.")
        self.name_formatter = NameFormatter(CHANNELS_CONFIG["emojis_formatting"])


    async def get_guild_by_id(self, guild_id: int) -> Optional[Guild]:
        """Вспомогательный метод для получения объекта Guild по ID."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            try:
                guild = await self.bot.fetch_guild(guild_id)
            except (discord.NotFound, discord.HTTPException) as e:
                logger.error(f"Не удалось получить гильдию {guild_id}: {e}")
                return None
        return guild

    def get_discord_channel_type(self, type_str: str) -> ChannelType:
        """Вспомогательный метод для получения типа канала Discord из строки."""
        type_map = {
            "text": ChannelType.text,
            "voice": ChannelType.voice,
            "category": ChannelType.category,
            "news": ChannelType.text,  # РЕФАКТОРИНГ: Создаем news как обычный текстовый канал
            "forum": ChannelType.text, # РЕФАКТОРИНГ: Создаем forum как обычный текстовый канал
        }
        return type_map.get(type_str.lower(), ChannelType.text)

    async def create_discord_category(self, guild: Guild, category_name: str, permissions: Optional[Dict[str, Any]]) -> CategoryChannel:
        """Создает новую категорию в Discord. Проверяет наличие перед созданием."""
        # Форматируем имя для поиска и создания в Discord
        formatted_category_name = self.name_formatter.format_name_for_discord(category_name, 'category')
        
        # Поиск существующей категории по ОТФОРМАТИРОВАННОМУ имени
        existing_category = utils.get(guild.categories, name=formatted_category_name)
        if existing_category:
            logger.info(f"Категория '{formatted_category_name}' уже существует. Используем существующую.")
            return existing_category

        # Настраиваем разрешения
        overwrites = {}
        if permissions:
            default_role_overwrite = discord.PermissionOverwrite()
            if 'view_channel' in permissions:
                default_role_overwrite.view_channel = permissions['view_channel']
            if 'read_messages' in permissions: # Often implies view_channel
                default_role_overwrite.read_messages = permissions['read_messages']
            if 'send_messages' in permissions:
                default_role_overwrite.send_messages = permissions['send_messages']
            if 'connect' in permissions:
                default_role_overwrite.connect = permissions['connect']
            if 'speak' in permissions:
                default_role_overwrite.speak = permissions['speak']
            if 'add_reactions' in permissions:
                default_role_overwrite.add_reactions = permissions['add_reactions']
            if 'use_external_emojis' in permissions:
                default_role_overwrite.use_external_emojis = permissions['use_external_emojis']
            if 'manage_channels' in permissions:
                default_role_overwrite.manage_channels = permissions['manage_channels']
            if 'manage_roles' in permissions:
                default_role_overwrite.manage_roles = permissions['manage_roles']
            if 'manage_messages' in permissions:
                default_role_overwrite.manage_messages = permissions['manage_messages']


            # Применяем к @everyone, если нет специфических настроек для других ролей
            overwrites[guild.default_role] = default_role_overwrite

        try:
            category_channel = await guild.create_category(name=formatted_category_name, overwrites=overwrites)
            logger.success(f"Создана категория: '{formatted_category_name}' (ID: {category_channel.id}).")
            return category_channel
        except (Forbidden, HTTPException) as e:
            logger.error(f"Ошибка Discord API при создании категории '{formatted_category_name}': {e}", exc_info=True)
            raise

    async def create_discord_channel(
        self, guild: Guild, channel_name: str, channel_type_str: str,
        parent_category: Optional[CategoryChannel] = None, permissions: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None, private_for_member: Optional[discord.Member] = None
    ) -> Optional[Union[TextChannel, VoiceChannel, ForumChannel]]:
        """Создает новый канал в Discord. Проверяет наличие перед созданием."""
        discord_channel_type = self.get_discord_channel_type(channel_type_str)
        
        # Имя канала для поиска в Discord (будет отформатировано)
        formatted_channel_name_for_lookup = self.name_formatter.format_name_for_discord(channel_name, discord_channel_type.name)
        
        # Discord API для create_channel требует имя без эмодзи, в нижнем регистре, с дефисами.
        # Вся логика очистки теперь перенесена в NameFormatter.normalize_name_from_discord.
        clean_name_for_api = self.name_formatter.normalize_name_from_discord(channel_name, discord_channel_type.name)
        
        # Если после очистки имя стало пустым, это проблема.
        if not clean_name_for_api:
            logger.error(f"Имя канала '{channel_name}' после нормализации для Discord API стало пустым. Пропуск создания.")
            return None # Или можно поднять ошибку, если это критично

        # Поиск существующего канала по ОТФОРМАТИРОВАННОМУ имени (как оно выглядит в Discord)
        # Если канал текстовый, ищем его без # (Discord API сам добавляет/удаляет #)
        existing_channel = utils.get(guild.channels, name=formatted_channel_name_for_lookup.lstrip('#'), category=parent_category)


        if existing_channel and existing_channel.type == discord_channel_type:
            logger.info(f"Канал '{formatted_channel_name_for_lookup}' уже существует. Используем существующий.")
            return existing_channel

        overwrites = {}
        if private_for_member:
            overwrites[private_for_member] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        elif permissions:
            default_role_overwrite = discord.PermissionOverwrite()
            if 'view_channel' in permissions:
                default_role_overwrite.view_channel = permissions['view_channel']
            if 'read_messages' in permissions:
                default_role_overwrite.read_messages = permissions['read_messages']
            if 'send_messages' in permissions:
                default_role_overwrite.send_messages = permissions['send_messages']
            if 'add_reactions' in permissions:
                default_role_overwrite.add_reactions = permissions['add_reactions']
            if 'use_external_emojis' in permissions:
                default_role_overwrite.use_external_emojis = permissions['use_external_emojis']
            if 'manage_channels' in permissions:
                default_role_overwrite.manage_channels = permissions['manage_channels']
            if 'manage_roles' in permissions:
                default_role_overwrite.manage_roles = permissions['manage_roles']
            if 'manage_messages' in permissions:
                default_role_overwrite.manage_messages = permissions['manage_messages']
            if 'connect' in permissions: # Для голосовых каналов
                default_role_overwrite.connect = permissions['connect']
            if 'speak' in permissions: # Для голосовых каналов
                default_role_overwrite.speak = permissions['speak']

            overwrites[guild.default_role] = default_role_overwrite
            
        # Общие аргументы для всех типов каналов
        channel_kwargs_common = {
            "name": clean_name_for_api, # Имя для Discord API (без эмодзи, в нижнем регистре)
            "category": parent_category,
            "overwrites": overwrites
        }
        if description: channel_kwargs_common["topic"] = description # "topic" это описание для текстовых, новостных, форумных каналов

        try:
            # РЕФАКТОРИНГ: Явный вызов guild.create_channel() для всех типов, передавая type аргумент.
            # Теперь все каналы, которые не являются голосовыми, будут создаваться как текстовые.
            if discord_channel_type == ChannelType.voice:
                channel_obj = await guild.create_voice_channel(**channel_kwargs_common)
            elif discord_channel_type == ChannelType.text: # Это включает text, news, forum из type_map
                channel_obj = await guild.create_text_channel(**channel_kwargs_common)
            else: # Для категорий и других типов, которые не должны быть здесь.
                logger.error(f"Попытка создать неподдерживаемый тип канала через create_discord_channel: {discord_channel_type.name}. Ожидается text или voice.")
                return None


            # Логируем ОТФОРМАТИРОВАННОЕ имя для читаемости в логах
            logger.success(f"Создан канал: '{formatted_channel_name_for_lookup}' (ID: {channel_obj.id}, Тип: {channel_type_str}).")
            return channel_obj
        except (Forbidden, HTTPException) as e:
            logger.error(f"Ошибка Discord API при создании канала '{formatted_channel_name_for_lookup}': {e}", exc_info=True)
            raise
            
    async def create_or_update_role(
        self, guild: discord.Guild, role_name: str,
        permissions_data: Optional[Dict[str, Any]] = None, # Изменено: теперь принимает словарь permissions_data
        color: Optional[discord.Color] = None, # Добавлено: опциональный цвет
        hoist: bool = False, mentionable: bool = False
    ) -> discord.Role:
        """
        Находит существующую роль по имени или создает новую с указанными параметрами.
        Принимает словарь permissions_data из конфига.
        """
        # Форматируем имя для поиска и создания в Discord (для ролей обычно нет спец. эмодзи, но на всякий случай)
        # Роли обычно не имеют спец. форматирования, поэтому NameFormatter может вернуть чистое имя.
        formatted_role_name = self.name_formatter.format_name_for_discord(role_name, 'role')

        existing_role = discord.utils.get(guild.roles, name=formatted_role_name)
        if existing_role:
            logger.info(f"Роль '{formatted_role_name}' уже существует. Используем существующую.")
            # Здесь можно добавить логику обновления, если это необходимо
            # if permissions_data: # Пример обновления разрешений, если нужно
            #     new_permissions = discord.Permissions.none()
            #     for perm, value in permissions_data.items():
            #         setattr(new_permissions, perm, value)
            #     await existing_role.edit(permissions=new_permissions, color=color or existing_role.color, hoist=hoist, mentionable=mentionable)
            return existing_role
        
        # Преобразуем словарь разрешений в объект discord.Permissions
        discord_permissions = discord.Permissions.none()
        if permissions_data:
            for perm, value in permissions_data.items():
                if hasattr(discord.Permissions, perm):
                    setattr(discord_permissions, perm, value)
                else:
                    logger.warning(f"Неизвестное разрешение Discord: {perm}")
        
        try:
            new_role = await guild.create_role(
                name=formatted_role_name, # Используем форматированное имя
                permissions=discord_permissions, # Передаем объект Permissions
                color=color or discord.Color.default(), # Используем переданный цвет или дефолтный
                hoist=hoist, mentionable=mentionable, reason="Создание роли по команде бота"
            )
            logger.success(f"Создана новая роль в Discord: '{new_role.name}' (ID: {new_role.id}).")
            return new_role
        except (Forbidden, HTTPException) as e:
            logger.error(f"Ошибка Discord API при создании роли '{formatted_role_name}': {e}", exc_info=True)
            raise

    async def delete_discord_entity(self, entity: Union[Role, CategoryChannel, TextChannel, VoiceChannel, ForumChannel]):
        """Универсально удаляет сущность Discord (роль, канал, категорию)."""
        try:
            entity_name = entity.name # Это имя, как оно сейчас в Discord (с форматированием)
            await entity.delete(reason="Удаление по команze бота.")
            logger.info(f"Сущность '{entity_name}' (ID: {entity.id}) успешно удалена из Discord.")
        except discord.NotFound:
            logger.warning(f"Сущность '{entity.name}' (ID: {entity.id}) не найдена, возможно уже удалена.")
        except Forbidden:
            logger.error(f"Нет прав на удаление сущности '{entity.name}'.")
            raise
        except HTTPException as e:
            logger.error(f"Ошибка Discord API при удалении сущности '{entity.name}': {e}")
            raise

    async def get_discord_object_by_id(self, guild: Guild, discord_id: int) -> Optional[Union[Role, CategoryChannel, TextChannel, VoiceChannel, ForumChannel]]:
        """Пытается найти объект Discord по его ID (роль, канал или категорию)."""
        obj = guild.get_channel(discord_id) or guild.get_role(discord_id)
        if obj:
            return obj
        
        try:
            # Попытка найти через fetch, если в кэше нет
            obj = await self.bot.fetch_channel(discord_id)
            return obj
        except (discord.NotFound, discord.HTTPException):
            pass # Если не нашли как канал, попробуем как роль

        try:
            # fetch_roles() возвращает список, нужно найти нужную
            all_roles = await guild.fetch_roles()
            obj = discord.utils.get(all_roles, id=discord_id)
            return obj
        except (discord.NotFound, discord.HTTPException):
            logger.warning(f"Не удалось найти сущность с ID {discord_id} ни как канал, ни как роль.")
        
        return None
            
    async def create_player_role(self, guild: discord.Guild, account_id: int) -> Optional[discord.Role]:
        """
        Создает на сервере новую роль для игрока с именем "Player-<account_id>".
        Если роль уже существует, возвращает ее.
        """
        role_name = f"Player-{account_id}" # Это имя не требует форматирования из конфига
        existing_role = discord.utils.get(guild.roles, name=role_name)
        if existing_role:
            logger.info(f"Роль '{role_name}' уже существует. Используем ее.")
            return existing_role

        try:
            new_role = await guild.create_role(name=role_name, reason=f"Создание роли для аккаунта {account_id}")
            logger.success(f"Создана роль '{role_name}' в гильдии '{guild.name}'.")
            return new_role
        except (Forbidden, HTTPException) as e:
            logger.error(f"Не удалось создать роль '{role_name}': {e}", exc_info=True)
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
            logger.info(f"Создана ссылка-приглашение для канала '{channel.name}': {invite.url}")
            return invite.url
        except (Forbidden, HTTPException) as e:
            logger.error(f"Не удалось создать приглашение для канала '{channel.name}': {e}", exc_info=True)
            return None

    async def send_dm_message(self, user: Union[Member, discord.User], message_content: str) -> bool:
        """
        Отправляет личное сообщение пользователю.
        """
        try:
            await user.send(message_content)
            logger.info(f"Отправлено личное сообщение пользователю {user.id} ({user.name}).")
            return True
        except (Forbidden, HTTPException) as e:
            logger.error(f"Не удалось отправить личное сообщение пользователю {user.id}: {e}")
            return False
