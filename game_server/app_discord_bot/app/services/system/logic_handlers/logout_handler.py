# game_server/app_discord_bot/app/services/system/logic_handlers/logout_handler.py

import inject
import discord
import logging

from game_server.app_discord_bot.app.constant.roles_blueprint import OFFLINE_ROLE, ONLINE_ROLE
from game_server.app_discord_bot.app.services.utils.role_finder import RoleFinder
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.contracts.dtos.system.commands import LogoutCharacterCommandDTO, LogoutCharacterPayload
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload

class LogoutHandler:
    """
    Обработчик для полноценного выхода персонажа из игры.
    Отправляет команду на бэкенд, затем меняет роли и чистит кэш.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: IAccountDataManager,
        character_cache_manager: ICharacterCacheManager,
        role_finder: RoleFinder,
        ws_manager: WebSocketManager,
        logger: logging.Logger
    ):
        self.account_data_manager = account_data_manager
        self.character_cache_manager = character_cache_manager
        self.role_finder = role_finder
        self.ws_manager = ws_manager
        self.logger = logger

    async def execute(self, payload: str, interaction: discord.Interaction):
        """
        Выполняет полный выход персонажа из игры.
        """
        user = interaction.user
        guild = interaction.guild
        self.logger.info(f"Инициирован полный выход из игры для пользователя {user.name}.")

        try:
            # 1. Получаем ID персонажа и аккаунта для команды
            character_id = await self.character_cache_manager.get_active_character_id(user.id)
            account_id_str = await self.account_data_manager.get_account_id_by_discord_id(user.id)

            if not character_id or not account_id_str:
                # Если сессии нет, просто сообщаем об этом, не вызывая ошибку
                await interaction.followup.send("Активная игровая сессия не найдена.", ephemeral=True)
                self.logger.warning(f"Попытка выхода для {user.name}, но активная сессия не найдена.")
                return None

            # 2. Отправляем команду на бэкенд
            logout_payload_data = LogoutCharacterPayload(character_id=character_id, account_id=int(account_id_str))
            command_dto = LogoutCharacterCommandDTO(payload=logout_payload_data) # <--- ИЗМЕНЕНИЕ ЗДЕСЬ
            
            response_data, _ = await self.ws_manager.send_command(
                command_type=command_dto.command,
                command_payload=command_dto.model_dump(), # model_dump() теперь корректно сериализует вложенный payload
                domain="system",
                discord_context={"user_id": user.id, "guild_id": guild.id}
            )

            ws_response = WebSocketResponsePayload(**response_data.get('payload', {}))
            if ws_response.status != ResponseStatus.SUCCESS:
                raise RuntimeError(f"Бэкенд вернул ошибку при выходе: {ws_response.message}")
            
            self.logger.info(f"Бэкенд успешно обработал выход для персонажа {character_id}.")

            # 3. Выполняем действия на стороне бота: меняем роли
            roles_data = await self.account_data_manager.get_account_field(guild.id, user.id, RedisKeys.FIELD_DISCORD_ROLES)
            personal_role_id = int(roles_data["personal_role_id"])
            
            offline_role = await self.role_finder.get_system_role(guild, OFFLINE_ROLE, shard_type="game")
            online_role = await self.role_finder.get_system_role(guild, ONLINE_ROLE, shard_type="game")
            personal_role = guild.get_role(personal_role_id)

            if online_role: await user.remove_roles(online_role, reason="Выход из игры")
            if personal_role: await user.remove_roles(personal_role, reason="Выход из игры")
            if offline_role: await user.add_roles(offline_role, reason="Выход из игры")
            
            # 4. Очищаем сессию из Redis
            await self.character_cache_manager.clear_login_session(user.id, guild.id)
            
            # 5. Отправляем финальный ответ
            await interaction.followup.send("Вы успешно вышли из игры. Ваш прогресс сохранен.", ephemeral=True)
            
            return None # Завершаем работу оркестратора
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка при выходе из игры для {user.name}: {e}", exc_info=True)
            # Отправляем сообщение об ошибке, если можем
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Произошла ошибка при выходе: {e}", ephemeral=True)
            else:
                await interaction.followup.send(f"Произошла ошибка при выходе: {e}", ephemeral=True)
            return None