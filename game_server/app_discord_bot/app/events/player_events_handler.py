# game_server/app_discord_bot/app/events/player_events_handler.py
import discord
import logging
import inject
from typing import Optional

from game_server.app_discord_bot.app.constant.constants_world import HUB_GUILD_ID
from game_server.app_discord_bot.app.constant.roles_blueprint import OFFLINE_ROLE, PLAYER_ROLE
from game_server.app_discord_bot.app.services.admin.base_discord_operations import BaseDiscordOperations
from game_server.app_discord_bot.storage.cache.managers.account_data_manager import AccountDataManager
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager 

class PlayerEventsHandler:
    """
    Обрабатывает события Discord, связанные с жизненным циклом игрока (вход на сервер, выход и т.д.).
    """
    @inject.autoparams()
    def __init__(
        self,
        base_ops: BaseDiscordOperations,
        account_data_manager: AccountDataManager,
        guild_config_manager: GuildConfigManager,
        logger: logging.Logger,
    ):
        self.base_ops = base_ops
        self.account_data_manager = account_data_manager
        self.guild_config_manager = guild_config_manager
        self.logger = logger
        self.logger.info("✨ PlayerEventsHandler инициализирован.")

    async def handle_player_join(self, member: discord.Member):
        """
        Полный цикл обработки входа нового игрока на игровой шард.
        Создает персональные роли и каналы и сохраняет их ID в Redis.
        """
        if member.guild.id == HUB_GUILD_ID:
            self.logger.info(f"Игрок {member.id} присоединился к Хабу. Пропускаю процесс подготовки игрока.")
            return

        self.logger.info(f"Новый участник {member.id} присоединился к шарду {member.guild.id}. Начинаю процесс подготовки...")

        try:
            account_id = await self.account_data_manager.get_account_id_by_discord_id(
                discord_user_id=member.id
            )
            
            if not account_id:
                self.logger.warning(f"Не удалось найти account_id для пользователя {member.id}. Процесс подготовки остановлен.")
                return

            # --- Шаг 1: Создание или обновление персональной роли ---
            # Получаем или создаем персональную роль для игрока
            personal_role = await self.base_ops.create_or_update_role(member.guild, f"Player-{account_id}")
            if not personal_role:
                self.logger.error(f"Не удалось создать персональную роль для {member.id}. Прерываю процесс.")
                return
            
            self.logger.info(f"Персональная роль '{personal_role.name}' для {member.id} создана/обновлена. Не выдается игроку.")


            # --- Шаг 2: Выдача базовых ролей (Offline, Player) ---
            # Эта логика остается, так как она не относится к персональной роли, управляющей каналами.
            offline_role_id = await self._get_cached_role_id(member.guild.id, OFFLINE_ROLE)
            player_role_id = await self._get_cached_role_id(member.guild.id, PLAYER_ROLE)

            offline_role_obj = member.guild.get_role(offline_role_id) if offline_role_id else None
            player_role_obj = member.guild.get_role(player_role_id) if player_role_id else None
            
            roles_to_add = [role for role in [offline_role_obj, player_role_obj] if role and role not in member.roles]
            
            if roles_to_add:
                await member.add_roles(*roles_to_add, reason="Первичная настройка игрока")
                self.logger.info(f"Выданы базовые роли для {member.id}.")
            else:
                self.logger.info(f"Базовые роли уже есть или не найдены для {member.id}.")
            
            # --- Шаг 3: Проверка и создание персональных каналов ---
            self.logger.debug(f"Проверяю/создаю персональные каналы для {member.id}.")
            
            # Получаем данные о каналах из Redis, если они уже существуют
            channels_data = await self.account_data_manager.get_account_field(
                shard_id=member.guild.id,
                discord_user_id=member.id,
                field_name="discord_channels"
            )

            interface_channel_id = channels_data.get("interface_channel_id") if channels_data and isinstance(channels_data, dict) else None
            dashboard_channel_id = channels_data.get("dashboard_channel_id") if channels_data and isinstance(channels_data, dict) else None

            # Используем member.guild для получения объекта гильдии
            interface_channel = member.guild.get_channel(int(interface_channel_id)) if interface_channel_id else None
            dashboard_channel = member.guild.get_channel(int(dashboard_channel_id)) if dashboard_channel_id else None

            # 🔥 ИЗМЕНЕНИЕ: Передаем personal_role в _provision_personal_channel
            if not interface_channel:
                interface_channel = await self._provision_personal_channel(member, personal_role, account_id, "INTERFACES", "interface")
                if interface_channel:
                    self.logger.info(f"Персональный канал 'interface-{account_id}' создан.")
            else:
                self.logger.info(f"Персональный канал 'interface-{account_id}' уже существует.")
            
            if not dashboard_channel:
                dashboard_channel = await self._provision_personal_channel(member, personal_role, account_id, "ARENAS_AND_LOGS", "dashboard")
                if dashboard_channel:
                    self.logger.info(f"Персональный канал 'dashboard-{account_id}' создан.")
            else:
                self.logger.info(f"Персональный канал 'dashboard-{account_id}' уже существует.")
            
            if not interface_channel or not dashboard_channel:
                self.logger.error(f"Не удалось создать один из личных каналов для {member.id}. Дальнейшая настройка невозможна.")
                return

            # --- Шаг 4: Сохранение данных в Redis по новой структуре ---
            self.logger.debug(f"Сохраняю ID сущностей в Redis для {member.id} по новой структуре.")
            
            # Сохраняем ID персональной роли
            roles_payload = {
                "personal_role_id": personal_role.id
            }
            channels_payload = {
                "interface_channel_id": str(interface_channel.id),
                "dashboard_channel_id": str(dashboard_channel.id)
            }

            await self.account_data_manager.save_account_field(member.guild.id, member.id, "discord_roles", roles_payload)
            await self.account_data_manager.save_account_field(member.guild.id, member.id, "discord_channels", channels_payload)
            
            self.logger.info(f"Сохранены ID ролей и каналов в отдельные поля для аккаунта {account_id}.")
            self.logger.success(f"Процесс подготовки для {member.id} (account_id: {account_id}) успешно завершен.")

        except Exception as e:
            self.logger.critical(f"Критическая ошибка при обработке входа {member.id} на шард {member.guild.id}: {e}", exc_info=True)

    async def _get_cached_role_id(self, guild_id: int, role_name: str) -> Optional[int]:
        """Внутренний метод для получения ID роли из кэша гильдии."""
        config = await self.guild_config_manager.get_field(guild_id, "system_roles", "game")
        role_data = config.get(role_name) if config and isinstance(config, dict) else None
        role_id = role_data.get("discord_id") if role_data and isinstance(role_data, dict) else None
        return role_id

    # Принимает personal_role (объект discord.Role)
    async def _provision_personal_channel(self, member: discord.Member, personal_role: discord.Role, account_id: int, cat_name: str, chan_name_prefix: str) -> Optional[discord.TextChannel]:
        """Создает один персональный канал."""
        guild_layout = await self.guild_config_manager.get_field(member.guild.id, "layout_config", "game")
        if not guild_layout:
            self.logger.error(f"layout_config для шарда {member.guild.id} не найден. Невозможно создать канал.")
            return None

        player_category_map = guild_layout.get("player_channel_category_map", {}) 
        category_id_str = player_category_map.get(cat_name)
        
        if not category_id_str:
            self.logger.error(f"Не удалось найти ID для категории '{cat_name}' в конфиге шарда {member.guild.id}.")
            return None
        
        category = member.guild.get_channel(int(category_id_str))
        if not category or not isinstance(category, discord.CategoryChannel):
            self.logger.error(f"Категория '{cat_name}' (ID: {category_id_str}) не найдена или не является категорией.")
            return None

        # Права доступа теперь для персональной роли, а не для самого пользователя
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(view_channel=False), # @everyone не видит
            personal_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, read_message_history=True) # Персональная роль видит
        }
        
        channel_name = f"{chan_name_prefix}-{account_id}"
        return await self.base_ops.create_discord_channel(member.guild, channel_name, "text", category, overwrites)
