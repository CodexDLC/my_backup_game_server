# game_server/app_discord_bot/app/services/authentication/lobby/logic_handlers/create_character_handler.py

import discord
import inject
import logging
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.contracts.dtos.character.commands import CreateNewCharacterCommandDTO, CreateNewCharacterPayload
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload

class CreateCharacterHandler:
    """
    Обработчик, отвечающий за отправку команды на создание нового персонажа.
    """
    @inject.autoparams()
    def __init__(self, ws_manager: WebSocketManager, logger: logging.Logger):
        self.ws_manager = ws_manager
        self.logger = logger

    async def execute(self, account_id: int, user: discord.User, guild: discord.Guild) -> int:
        """
        Отправляет команду на создание персонажа и возвращает его ID.
        """
        self.logger.info(f"Инициировано создание персонажа для аккаунта {account_id}.")
        
        payload_data = CreateNewCharacterPayload(
            account_id=account_id,
            discord_user_id=user.id,
            guild_id=guild.id
        )
        creation_dto = CreateNewCharacterCommandDTO(payload=payload_data)

        # Добавляем `discord_context` в вызов
        response_data, _ = await self.ws_manager.send_command(
            command_type=creation_dto.command,
            command_payload=creation_dto.model_dump(),
            domain="system",
            discord_context={"user_id": user.id, "guild_id": guild.id}
        )
        
        # 3. Обрабатываем ответ
        response_payload = WebSocketResponsePayload(**response_data.get('payload', {}))
        if response_payload.status != ResponseStatus.SUCCESS:
            self.logger.error(f"Ошибка на этапе создания персонажа: {response_payload.message}")
            raise RuntimeError(f"Ошибка на этапе создания персонажа: {response_payload.message}")

        character_id = response_payload.data.get("character_id")
        if not character_id:
            self.logger.error("Бэкенд не вернул ID персонажа после создания.")
            raise RuntimeError("Не удалось получить ID персонажа после создания.")

        self.logger.info(f"Персонаж {character_id} успешно создан на бэкенде.")
        return character_id