# game_server/app_discord_bot/app/services/authentication/logic_handlers/login_start.py

import inject
import discord
from discord.ext import commands

from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors
from game_server.app_discord_bot.core.contracts.handler_response_dto import InitialLobbySetupDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

# 🔥 ИЗМЕНЕНО: Импортируем новое DTO команды и результата
from game_server.contracts.api_models.character.responses import CharacterListResponseData
from game_server.contracts.dtos.system.commands import GetCharacterListForAccountCommandDTO


from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketMessage, WebSocketResponsePayload
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager


class LoginStartHandler:
    """
    Обработчик логики для старта сессии игрока.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: IAccountDataManager,
        ws_manager: WebSocketManager,
        interaction_response_manager: InteractionResponseManager,
    ):
        self.account_data_manager = account_data_manager
        self.ws_manager = ws_manager
        self.interaction_response_manager = interaction_response_manager
        
    @handle_flow_errors
    async def execute(self, payload: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        user = interaction.user
        guild = interaction.guild
        
        # --- НОВАЯ ПРОВЕРКА ---
        if user.mobile_status != discord.Status.offline:
            await self.interaction_response_manager.send_personal_notification_message(
                interaction,
                "**Внимание!** Похоже, вы используете мобильную версию Discord.\n\n"
                "Из-за её особенностей, игровой интерфейс может не обновиться сразу. "
                "Если вы не видите меню выбора персонажа, пожалуйста, **полностью перезапустите приложение Discord**.",
                delete_after=60
            )
            # Мы НЕ прерываем выполнение, логин продолжится в фоне.
        # --- КОНЕЦ ПРОВЕРКИ ---
        
        try:
            account_id_str = await self.account_data_manager.get_account_id_by_discord_id(user.id)
            if not account_id_str:
                raise ValueError("Ваш игровой аккаунт не найден. Пожалуйста, убедитесь, что вы зарегистрированы.")
            
            account_id = int(account_id_str)

            # 🔥 ИЗМЕНЕНО: Используем новое DTO команды
            command_dto = GetCharacterListForAccountCommandDTO(account_id=account_id)
            
            full_message_dict, _ = await self.ws_manager.send_command(
                command_type=command_dto.command,
                command_payload=command_dto.model_dump(),
                domain="system", # 🔥 ИЗМЕНЕНО: domain с "auth" на "system"
                discord_context={"user_id": user.id, "guild_id": guild.id}
            )

            response_payload_dict = full_message_dict.get('payload', {})
            ws_response_payload = WebSocketResponsePayload(**response_payload_dict)
            
            if ws_response_payload.status != ResponseStatus.SUCCESS:
                error_message = ws_response_payload.message or "Неизвестная ошибка при запросе данных сессии."
                raise RuntimeError(error_message)
            
            # 🔥 ИЗМЕНЕНО: Используем новое DTO результата
            result_data = CharacterListResponseData(**ws_response_payload.data)
            
            # Возвращаем DTO с результатом
            return InitialLobbySetupDTO(
                type="initial_lobby_setup",
                characters=result_data.characters
            )
        except Exception as e:
            # Если произошла ошибка здесь, мы отправляем персональное уведомление
            # и удаляем индикатор.
            await self.interaction_response_manager.send_personal_notification_message(
                interaction,
                f"Произошла ошибка при входе в лобби: {e}",
                delete_after=None
            )
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return None
