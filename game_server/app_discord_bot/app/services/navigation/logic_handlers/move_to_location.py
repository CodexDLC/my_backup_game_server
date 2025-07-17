# game_server/app_discord_bot/app/services/navigation/logic_handlers/move_to_location.py
# Version: 0.007 # Увеличиваем версию

import inject
import discord
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Менеджеры кэша
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager

# DTOs для взаимодействия с бэкендом
from game_server.contracts.dtos.game_commands.navigation_commands import MoveToLocationPayloadDTO, MoveToLocationCommandDTO, MoveToLocationResultDTO

# Внутренние DTOs бота
from game_server.app_discord_bot.app.services.navigation.dtos import NavigationDisplayDataDTO

# Хелперы и сервисы (используем WebSocketManager)
from game_server.app_discord_bot.app.services.utils.navigation_helper import NavigationHelper
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager

# Импортируем ShowNavigationHandler для последующего вызова
from game_server.app_discord_bot.app.services.navigation.logic_handlers.show_navigation import ShowNavigationHandler
from game_server.contracts.shared_models.base_responses import ResponseStatus, ErrorDetail
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload


class MoveToLocationHandler:
    """
    Логический обработчик для команды перемещения персонажа в новую локацию.
    Отправляет запрос на бэкенд, обновляет Redis и инициирует обновление UI.
    Теперь также обрабатывает команду 'back'.
    """
    @inject.autoparams()
    def __init__(
        self,
        character_cache_manager: ICharacterCacheManager,
        account_data_manager: IAccountDataManager,
        navigation_helper: NavigationHelper,
        ws_manager: WebSocketManager,
        show_navigation_handler: ShowNavigationHandler,
        game_world_data_manager: IGameWorldDataManager,
        logger: logging.Logger
    ):
        self.character_cache_manager = character_cache_manager
        self.account_data_manager = account_data_manager
        self.navigation_helper = navigation_helper
        self.ws_manager = ws_manager
        self.show_navigation_handler = show_navigation_handler
        self.game_world_data_manager = game_world_data_manager
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def execute(self, command_str: str, interaction: discord.Interaction) -> NavigationDisplayDataDTO:
        """
        Выполняет логику перемещения персонажа.

        Args:
            command_str (str): Строка команды (ожидается "move_to:<target_location_id>" или "back").
            interaction (discord.Interaction): Объект взаимодействия Discord.

        Returns:
            NavigationDisplayDataDTO: DTO с данными для отображения новой локации.

        Raises:
            ValueError: Если не удалось получить необходимые данные или перемещение не удалось.
        """
        user = interaction.user
        guild = interaction.guild
        self.logger.debug(f"Выполняется MoveToLocationHandler для пользователя {user.name} с командой: {command_str}")

        target_location_id: Optional[str] = None
        
        try:
            # 1. Определение целевой локации на основе command_str
            if command_str.startswith("move_to:"):
                parts = command_str.split(":")
                if len(parts) < 2 or not parts[1]:
                    raise ValueError("Неверный формат команды 'move_to'. Ожидается 'move_to:<location_id>'.")
                target_location_id = parts[1]
                self.logger.debug(f"Команда 'move_to' с целевой локацией: {target_location_id}")
            elif command_str == "back":
                self.logger.debug(f"Обработка команды 'back' для пользователя {user.name}.")
                character_id_for_back = await self.character_cache_manager.get_active_character_id(user.id)
                if not character_id_for_back:
                    raise ValueError(f"Не найден активный персонаж для пользователя {user.name} для команды 'back'.")

                char_session_for_back = await self.character_cache_manager.get_character_session(character_id_for_back, guild.id)
                previous_location_data = char_session_for_back.get("location", {}).get("previous", {})
                
                if previous_location_data and previous_location_data.get("location_id"):
                    target_location_id = previous_location_data["location_id"]
                    self.logger.info(f"Команда 'back': перемещение в предыдущую локацию: {target_location_id}.")
                else:
                    raise ValueError("Невозможно вернуться назад: нет данных о предыдущей локации.")
            else:
                raise ValueError(f"Неизвестная команда навигации: '{command_str}'.")

            if not target_location_id:
                raise ValueError("Не удалось определить целевую локацию для перемещения.")

            # 2. Получаем ID персонажа и аккаунта (общая логика для move_to и back)
            character_id = await self.character_cache_manager.get_active_character_id(user.id)
            if not character_id:
                raise ValueError(f"Не найден активный персонаж для пользователя {user.name}.")
            
            active_session_data = await self.character_cache_manager._redis.hgetall(
                RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=user.id)
            )
            account_id_str = active_session_data.get(RedisKeys.FIELD_SESSION_ACCOUNT_ID)
            if not account_id_str:
                raise ValueError(f"Не найден account_id для пользователя {user.name} в активной сессии.")
            account_id = int(account_id_str)

            # Получаем текущую локацию для обновления поля 'previous'
            character_session = await self.character_cache_manager.get_character_session(character_id, guild.id)
            current_location_data = character_session.get("location", {}).get("current", {})
            old_location_id = current_location_data.get("location_id")
            old_region_id = current_location_data.get("region_id")


            if old_location_id == target_location_id:
                self.logger.info(f"Персонаж {character_id} уже находится в локации {target_location_id}. Обновление не требуется.")
                return await self.show_navigation_handler.execute("show_navigation", interaction)

            # 3. Формируем DTO для бэкенда
            payload = MoveToLocationPayloadDTO(
                character_id=character_id,
                account_id=account_id,
                target_location_id=target_location_id
            )
            command_to_backend = MoveToLocationCommandDTO(payload=payload)

            self.logger.debug(f"Отправка команды перемещения на бэкенд: {command_to_backend.model_dump_json()}")
            
            # 4. Отправляем команду на бэкенд и ждем результат
            response_data_raw, _ = await self.ws_manager.send_command(
                command_type=command_to_backend.command,
                command_payload=command_to_backend.model_dump(),
                domain="system",
                discord_context={"user_id": user.id, "guild_id": guild.id}
            )
            
            response_payload_ws = WebSocketResponsePayload(**response_data_raw.get('payload', {}))

            backend_result = MoveToLocationResultDTO(
                correlation_id=response_payload_ws.request_id,
                success=response_payload_ws.status == ResponseStatus.SUCCESS,
                message=response_payload_ws.message,
                data=response_payload_ws.data,
                error=response_payload_ws.error
            )

            if not backend_result.success:
                error_message = backend_result.message or "Неизвестная ошибка при перемещении."
                if backend_result.error:
                    error_message += f" (Код: {backend_result.error.code}, Детали: {backend_result.error.message})"
                self.logger.error(f"Бэкенд вернул ошибку при перемещении персонажа {character_id} в {target_location_id}: {error_message}")
                raise ValueError(f"Не удалось переместиться: {error_message}")

            self.logger.info(f"Персонаж {character_id} успешно перемещен в локацию {target_location_id} по подтверждению бэкенда.")

            # 🔥 НОВОЕ: Обновляем динамические данные для ПРЕДЫДУЩЕЙ локации 🔥
            if old_location_id and old_location_id != target_location_id:
                self.logger.debug(f"Обновление динамических данных для предыдущей локации: {old_location_id}")
                old_location_dynamic_data = await self.game_world_data_manager.get_dynamic_location_data(old_location_id)
                if old_location_dynamic_data:
                    players_in_old_location = old_location_dynamic_data.get("players_in_location", 0)
                    if players_in_old_location > 0:
                        old_location_dynamic_data["players_in_location"] = players_in_old_location - 1
                        old_location_dynamic_data["last_update"] = datetime.now() # Обновляем время последнего изменения
                        await self.game_world_data_manager.set_dynamic_location_data(old_location_id, old_location_dynamic_data)
                        self.logger.info(f"Уменьшено количество игроков в предыдущей локации {old_location_id} до {old_location_dynamic_data['players_in_location']}.")
                    else:
                        self.logger.warning(f"Попытка уменьшить количество игроков в {old_location_id}, но оно уже 0 или меньше.")
                else:
                    self.logger.warning(f"Не удалось получить динамические данные для предыдущей локации {old_location_id} для обновления.")


            # 5. Обновляем Redis: current и previous локации в сессии персонажа
            updated_location_data = {
                "current": {"location_id": target_location_id, "region_id": old_region_id},
                "previous": {"location_id": old_location_id, "region_id": old_region_id}
            }
            char_session_key = RedisKeys.CHARACTER_SESSION_HASH.format(guild_id=guild.id, character_id=character_id)
            await self.character_cache_manager._redis.hset(char_session_key, "location", json.dumps(updated_location_data))
            
            self.logger.debug(f"Redis сессии персонажа обновлен: персонаж {character_id} теперь в {target_location_id}, предыдущая: {old_location_id}.")

            # 6. Сохраняем ambient_footer_data в GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA в Redis бота (для НОВОЙ локации)
            if backend_result.data and "ambient_footer_data" in backend_result.data:
                ambient_data_from_backend = backend_result.data["ambient_footer_data"]
                # Убедимся, что last_update присутствует и является datetime
                if "last_update" not in ambient_data_from_backend:
                    ambient_data_from_backend["last_update"] = datetime.now()
                # Если players_in_location или npcs_in_location отсутствуют, инициализируем их
                if "players_in_location" not in ambient_data_from_backend:
                    ambient_data_from_backend["players_in_location"] = 1 # Предполагаем, что игрок вошел
                if "npcs_in_location" not in ambient_data_from_backend:
                    ambient_data_from_backend["npcs_in_location"] = 0 # Или другое дефолтное значение

                await self.game_world_data_manager.set_dynamic_location_data(
                    location_id=target_location_id,
                    data=ambient_data_from_backend
                )
                self.logger.debug(f"Динамические данные для локации {target_location_id} сохранены в Redis бота (как хеш).")
            else:
                self.logger.warning(f"Ambient_footer_data не получены из бэкенда для локации {target_location_id}.")


            # 7. Вызываем ShowNavigationHandler для отображения новой локации
            return await self.show_navigation_handler.execute("show_navigation", interaction)

        except ValueError as e:
            self.logger.error(f"Ошибка перемещения для пользователя {user.name}: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"Критическая ошибка в MoveToLocationHandler для {user.name}: {e}", exc_info=True)
            raise