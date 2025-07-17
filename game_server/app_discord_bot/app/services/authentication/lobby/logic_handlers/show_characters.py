#  game_server\app_discord_bot\app\services\authentication\lobby\logic_handlers\show_characters.py

import inject
import discord
from discord.ext import commands

from game_server.app_discord_bot.core.contracts.handler_response_dto import CharacterSelectionDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

# 🔥 ИЗМЕНЕНО: Импортируем новое DTO команды и результата



from game_server.contracts.api_models.character.responses import CharacterListResponseData
from game_server.contracts.dtos.system.commands import GetCharacterListForAccountCommandDTO
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors


class ShowCharactersHandler:
    """
    Обработчик логики для команды 'Персонажи'.
    Получает список персонажей игрока через WebSocket.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: IAccountDataManager,
        ws_manager: WebSocketManager,
    ):
        self.account_data_manager = account_data_manager
        self.ws_manager = ws_manager

    @handle_flow_errors
    async def execute(self, payload: str, interaction: discord.Interaction):
        user = interaction.user
        guild = interaction.guild

        print(f"[+] Logic Handler (show_characters): Вызвана для пользователя {user.name}.")

        account_id_str = await self.account_data_manager.get_account_id_by_discord_id(user.id)
        if not account_id_str:
            raise ValueError("Ваш игровой аккаунт не найден. Пожалуйста, убедитесь, что вы зарегистрированы.")

        account_id = int(account_id_str)

        # 🔥 ИЗМЕНЕНО: Используем новое DTO команды
        command_dto = GetCharacterListForAccountCommandDTO(account_id=account_id)

        full_message_dict, _ = await self.ws_manager.send_command(
            command_type=command_dto.command, # command_dto.command теперь "get_character_list_for_account"
            command_payload=command_dto.model_dump(),
            domain="system", # domain должен быть "system", так как мы перенесли это туда
            discord_context={"user_id": user.id, "guild_id": guild.id}
        )

        response_payload_dict = full_message_dict.get('payload', {})
        ws_response_payload = WebSocketResponsePayload(**response_payload_dict)

        if ws_response_payload.status != ResponseStatus.SUCCESS:
            error_message = ws_response_payload.message or "Неизвестная ошибка при запросе данных персонажей."
            raise RuntimeError(error_message)

        # 🔥 ИЗМЕНЕНО: Используем новое DTO результата
        result_data = CharacterListResponseData(**ws_response_payload.data)

        # Возвращаем DTO с полученными персонажами
        return CharacterSelectionDTO(
            type="character_selection_view",
            characters=result_data.characters
        )