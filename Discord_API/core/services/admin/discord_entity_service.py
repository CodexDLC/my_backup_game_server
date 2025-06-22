# Discord_API/core/services/admin/discord_entity_service.py

from typing import Dict, Any, Optional, List
import discord

# Импортируем наш централизованный логгер
from Discord_API.config.logging.logging_setup_discod import logger
discord_entity_service_logger = logger.getChild(__name__)

# Импортируем специализированные сервисы
from Discord_API.core.services.admin.game_server_layout_service import GameServerLayoutService
from Discord_API.core.services.admin.role_management_service import RoleManagementService
from Discord_API.core.services.admin.hub_layout_service import HubLayoutService
from Discord_API.core.services.admin.base_discord_operations import BaseDiscordOperations

from Discord_API.core.services.admin.article_management_service import ArticleManagementService



class DiscordEntityService:
    """
    Оркестратор/Фасад для всех операций, связанных с сущностями Discord.
    Предоставляет высокоуровневые методы для команд Discord-бота,
    делегируя вызовы специализированным внутренним сервисам.
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        discord_entity_service_logger.info("Инициализация DiscordEntityService (Оркестратора).")

        # Инициализация специализированных сервисов
        self.hub_layout_manager = HubLayoutService(self.bot) # Инициализируем HubLayoutService
        self.game_server_layout_manager = GameServerLayoutService(self.bot)
        self.article_manager = ArticleManagementService(self.bot)
        self.role_manager = RoleManagementService(self.bot)
        self.base_ops = BaseDiscordOperations(self.bot) # Инициализируем BaseDiscordOperations
        
        discord_entity_service_logger.info("Специализированные менеджеры инициализированы.")

    async def setup_hub_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает полную структуру хаб-сервера в Discord и синхронизирует с бэкендом.
        Делегирует вызов HubLayoutService.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на развертывание Hub Layout для гильдии {guild_id}.")
        return await self.hub_layout_manager.setup_hub_layout(guild_id)

    async def setup_game_server_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Разворачивает минимальную структуру для игрового сервера (шарда) в Discord
        и синхронизирует с бэкендом.
        Делегирует вызов GameServerLayoutService.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на развертывание Game Server Layout для гильдии {guild_id}.")
        return await self.game_server_layout_manager.setup_game_server_layout(guild_id)

    async def teardown_discord_layout(self, guild_id: int) -> Dict[str, Any]:
        """
        Полностью удаляет все Discord сущности, связанные с данной гильдией.
        Делегирует вызов HubLayoutService.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на полное удаление лейаута для гильгии {guild_id}.")
        # ИСПРАВЛЕНО: Вызов teardown_discord_layout теперь направлен на self.hub_layout_manager
        return await self.hub_layout_manager.teardown_discord_layout(guild_id)

    async def add_article_channel(self, guild_id: int, channel_name: str) -> Dict[str, Any]:
        """
        Добавляет новый текстовый канал-статью в "Библиотеку Знаний" и синхронизирует с бэкендом.
        Делегирует вызов ArticleManagementService.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на добавление статьи '{channel_name}' для гильдии {guild_id}.")
        return await self.article_manager.add_article_channel(guild_id, channel_name)

    async def sync_discord_roles(self, guild_id: int) -> Dict[str, Any]:
        """
        Синхронизирует Discord роли для указанной гильдии на основе `state_entities`.
        Делегирует вызов RoleManagementService.
        Возвращает структурированный словарь результата.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на синхронизацию ролей для гильдии {guild_id}.")
        return await self.role_manager.sync_discord_roles(guild_id)

    async def delete_discord_roles_batch(self, guild_id: int, role_ids: List[int]) -> Dict[str, Any]:
        """
        Удаляет список ролей из Discord и соответствующие записи из БД.
        Делегирует вызов RoleManagementService.
        """
        discord_entity_service_logger.info(f"Оркестратор: Запрос на массовое удаление ролей для гильдии {guild_id}.")
        return await self.role_manager.delete_discord_roles_batch(guild_id, role_ids)

    async def onboard_player(
        self,
        guild_id: int,
        member_id: int,
        welcome_channel_name: str = "welcome-room",
        player_category_name: str = "Личные Каналы Игроков",
        new_player_role_name: str = "Новичок",
        player_role_name: str = "Игрок"
    ) -> Dict[str, Any]:
        """
        Обрабатывает нового игрока: меняет роли, скрывает приветственный канал,
        создает личный канал.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")
        
        member = guild.get_member(member_id)
        if not member:
            member = await guild.fetch_member(member_id)
            if not member:
                raise ValueError(f"Пользователь с ID {member_id} не найден в гильдии {guild.name}.")

        onboarding_results = {
            "role_update": {},
            "welcome_channel_hide": {},
            "personal_channel_create": {},
            "errors": []
        }

        discord_entity_service_logger.info(f"Начало онбординга пользователя '{member.display_name}' (ID: {member.id}).")

        try:
            role_update_result = await self.role_manager.assign_player_role_and_remove_new_player_role(
                member, new_player_role_name, player_role_name
            )
            onboarding_results["role_update"] = role_update_result
            if role_update_result.get("status") == "error":
                onboarding_results["errors"].append({"step": "role_update", "message": role_update_result.get("message")})
        except Exception as e:
            discord_entity_service_logger.error(f"Ошибка при смене ролей для {member.display_name}: {e}", exc_info=True)
            onboarding_results["errors"].append({"step": "role_update", "message": f"Непредвиденная ошибка: {e}"})

        try:
            welcome_channel = discord.utils.get(guild.text_channels, name=welcome_channel_name)
            if welcome_channel:
                hide_result = await self.base_ops.set_channel_visibility_for_role_or_member(
                    welcome_channel, guild.default_role, view_channel=False
                )
                onboarding_results["welcome_channel_hide"] = hide_result
                if hide_result.get("status") == "error":
                    onboarding_results["errors"].append({"step": "welcome_channel_hide", "message": hide_result.get("message")})
            else:
                discord_entity_service_logger.warning(f"Приветственный канал '{welcome_channel_name}' не найден. Пропускаем его скрытие.")
                onboarding_results["welcome_channel_hide"] = {"status": "skipped", "message": "Канал не найден."}
        except Exception as e:
            discord_entity_service_logger.error(f"Ошибка при скрытии приветственного канала для {member.display_name}: {e}", exc_info=True)
            onboarding_results["errors"].append({"step": "welcome_channel_hide", "message": f"Непредвиденная ошибка: {e}"})

        try:
            personal_channel_name = f"канал-{member.name.lower().replace(' ', '-')}"
            
            player_category = discord.utils.get(guild.categories, name=player_category_name)
            if not player_category:
                discord_entity_service_logger.info(f"Категория '{player_category_name}' не найдена, создаю...")
                # Предполагаем, что create_discord_category также принимает permissions для приватных категорий
                player_category_result = await self.base_ops.create_discord_category(guild, player_category_name, permissions="player_only_category") # Новый тип разрешения для приватных категорий игроков
                if player_category_result:
                    player_category = player_category_result
                else:
                    raise RuntimeError(f"Не удалось создать категорию '{player_category_name}'.")

            if player_category:
                personal_channel_create_result = await self.base_ops.create_discord_channel(
                    guild,
                    personal_channel_name,
                    "text",
                    parent_category=player_category,
                    private_for_member=member
                )
                if personal_channel_create_result:
                    onboarding_results["personal_channel_create"] = {"status": "success", "message": f"Личный канал '{personal_channel_name}' создан."}
                else:
                    onboarding_results["personal_channel_create"] = {"status": "error", "message": "Не удалось создать личный канал."}
                    onboarding_results["errors"].append({"step": "personal_channel_create", "message": "Не удалось создать личный канал."})
            else:
                onboarding_results["errors"].append({"step": "personal_channel_create", "message": "Не удалось найти или создать категорию для личных каналов."})

        except Exception as e:
            discord_entity_service_logger.error(f"Ошибка при создании личного канала для {member.display_name}: {e}", exc_info=True)
            onboarding_results["errors"].append({"step": "personal_channel_create", "message": f"Непредвиденная ошибка: {e}"})

        overall_status = "success" if not onboarding_results["errors"] else "partial_success"
        overall_message = "Онбординг игрока завершен." if not onboarding_results["errors"] else "Онбординг игрока завершен с ошибками."

        return {
            "status": overall_status,
            "message": overall_message,
            "details": onboarding_results
        }
