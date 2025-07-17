# game_server/app_discord_bot/app/services/authentication/lobby/logic_handlers/select_character.py

import inject
import discord
import logging

from game_server.app_discord_bot.core.contracts.handler_response_dto import AdventureStartedDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors

# --- ИЗМЕНЕНИЕ: Добавляем импорт ICharacterCacheManager ---
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager

# Обновленные импорты DTO
from game_server.contracts.dtos.auth.commands import LoginCharacterByIdCommandDTO, LoginCharacterByIdPayload
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload

class SelectCharacterHandler:
    """
    Обработчик для входа в мир выбранным персонажем.
    Делегирует кэширование сессии в CharacterCacheManager.
    """
    @inject.autoparams()
    def __init__(
        self, 
        account_data_manager: IAccountDataManager, 
        ws_manager: WebSocketManager, 
        logger: logging.Logger,
        # --- ИЗМЕНЕНИЕ: Инжектируем менеджер кэша персонажей ---
        character_cache_manager: ICharacterCacheManager
    ):
        self.account_data_manager = account_data_manager
        self.ws_manager = ws_manager
        self.logger = logger
        self.character_cache_manager = character_cache_manager

    @handle_flow_errors
    async def execute(self, payload_str: str, interaction: discord.Interaction) -> AdventureStartedDTO:
        user = interaction.user
        guild = interaction.guild
        self.logger.info(f"Игрок {user.name} входит в мир...")

        # 1. Извлекаем character_id из payload
        try:
            parts = payload_str.split(':')
            if len(parts) < 2 or parts[0] != "enter_world":
                raise ValueError("Некорректный формат команды.")
            character_id = int(parts[1])
        except (ValueError, IndexError):
            raise ValueError(f"Некорректный формат команды 'enter_world': {payload_str}.")

        # 2. Находим account_id по discord_id из кэша
        account_id_str = await self.account_data_manager.get_account_id_by_discord_id(user.id)
        if not account_id_str:
            raise ValueError("Ваш игровой аккаунт не найден...")
        account_id = int(account_id_str)
        
        # 3. Отправляем команду на логин
        login_payload_data = LoginCharacterByIdPayload(character_id=character_id, account_id=account_id)
        login_command_dto = LoginCharacterByIdCommandDTO(payload=login_payload_data)
        
        login_response, _ = await self.ws_manager.send_command(
            command_type=login_command_dto.command,
            command_payload=login_command_dto.model_dump(),
            domain="auth",
            discord_context={"user_id": user.id, "guild_id": guild.id}
        )
        
        response_payload = WebSocketResponsePayload(**login_response.get('payload', {}))
        if response_payload.status != ResponseStatus.SUCCESS:
            raise RuntimeError(response_payload.message or "Ошибка на этапе логина персонажа.")
            
        # --- ИЗМЕНЕНИЕ: Вся логика кэширования заменена одним вызовом ---
        character_data = response_payload.data.get("character_document")
        if not character_data:
            raise RuntimeError("Не получены данные персонажа для создания сессии.")

        # 4. Вызываем менеджер кэша, передавая все необходимые данные
        await self.character_cache_manager.cache_login_session(
            character_data=character_data,
            user_id=user.id,
            guild_id=guild.id,
            account_id=account_id # Передаем account_id, как требует новый интерфейс
        )

        self.logger.info(f"Сессия для персонажа ID {character_id} успешно создана/обновлена.")

        return AdventureStartedDTO(type="display_initial_location", discord_user_id=user.id)