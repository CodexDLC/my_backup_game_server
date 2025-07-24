# game_server/app_discord_bot/app/services/game_modules/inspection/logic_handlers/list_category.py

import discord
import inject
import logging
import json
from typing import Dict, Any, Optional, List

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import InspectedEntityDTO, InspectionListDTO, PaginationInfoDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheDiscordManager
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager


class ListCategoryHandler:
    """
    Обрабатывает команду 'list_category'.
    Запрашивает у бэкенда список сущностей в указанной категории и возвращает его для отображения.
    """
    ITEMS_PER_PAGE = 20

    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        account_data_manager: IAccountDataManager,
        character_cache_manager: ICharacterCacheDiscordManager,
        game_world_data_manager: IGameWorldDataManager
    ):
        self.logger = logger
        self.account_data_manager = account_data_manager
        self.character_cache_manager = character_cache_manager
        self.game_world_data_manager = game_world_data_manager
        
        # Соответствие ключа категории из команды на ключ поля в хеше Redis
        self.category_to_redis_field = {
            "players": "players",
            "npc_neutral": "npcs", # Пример, здесь могут быть разные виды npc
            "npc_enemy": "monsters" # Пример
            # Добавьте другие по необходимости
        }
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    def _get_mock_entity_details(self, entity_id: str, category_key: str) -> Dict[str, Any]:
        """
        ЗАГЛУШКА: Имитирует запрос к бэкенду за деталями НЕ-ИГРОВЫХ сущностей.
        Эта функция будет использоваться, пока мы не определим, как получать реальные данные для NPC, монстров и т.д.
        """
        self.logger.info(f"[ЗАГЛУШКА] Запрос деталей для сущности ID: '{entity_id}', Категория: '{category_key}'")
        return {
            "name": f"{category_key.capitalize()} #{entity_id}",
            "description": "Детальная информация для этой сущности пока не доступна.",
            "type": "Неизвестно"
        }

    async def _get_player_details(self, character_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает и форматирует детали для одного игрока из его сессии в Redis.
        """
        session_data = await self.character_cache_manager.get_character_session(character_id, guild_id)
        if not session_data:
            return None
        
        try:
            core_data = json.loads(session_data.get("core", "{}"))
            # stats_data = json.loads(session_data.get("stats", "{}")) # Если нужен уровень или другие статы
            
            return {
                "name": core_data.get("name", f"Игрок #{character_id}"),
                "level": "N/A" # TODO: Определить, откуда брать уровень
            }
        except json.JSONDecodeError:
            self.logger.error(f"Ошибка декодирования JSON для сессии персонажа {character_id}")
            return None

    async def execute(self, command_str: str, interaction: discord.Interaction) -> Optional[InspectionListDTO]:
        self.logger.info(f"Обработка команды '{command_str}' для пользователя {interaction.user.id}")

        parts = command_str.split(':')
        category_key = parts[1] if len(parts) > 1 else None
        page = int(parts[3]) if len(parts) > 3 and parts[2] == 'page' else 1
        
        if not category_key:
            self.logger.error(f"Не удалось извлечь ключ категории из команды: {command_str}")
            return None

        try:
            # --- Шаги 1, 2, 3 (получение ID и пагинация) ---
            active_session = await self.account_data_manager.get_active_session(interaction.user.id)
            if not active_session: return None
            
            char_session = await self.character_cache_manager.get_character_session(active_session["character_id"], interaction.guild_id)
            if not char_session: return None

            location_data = char_session["location"]
            current_location_id = location_data.get("current", {}).get("location_id")
            if not current_location_id: return None

            location_key = f"global:game_world_data_dynamic:{current_location_id}"
            redis_field = self.category_to_redis_field.get(command_str.split(':')[1])
            if not redis_field: return None
            
            location_hash = await self.game_world_data_manager.get_all_hash_fields(location_key)
            all_entities_data = json.loads(location_hash.get(redis_field, "[]"))

            if not all_entities_data: return None

            page = int(command_str.split(':')[-1]) if 'page' in command_str else 1
            total_pages = (len(all_entities_data) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
            start_index = (page - 1) * self.ITEMS_PER_PAGE
            paginated_data = all_entities_data[start_index:start_index + self.ITEMS_PER_PAGE]

            # --- Шаг 4: Получение деталей и формирование списка ---
            entities_list = []
            category_key = command_str.split(':')[1]

            if category_key == "players":
                paginated_ids = [int(entity["player_id"]) for entity in paginated_data if entity.get("player_id")]
                
                # ОДИН ПРОСТОЙ ВЫЗОВ
                details_map = await self.character_cache_manager.get_bulk_character_details(paginated_ids, interaction.guild_id)

                for player_id in paginated_ids:
                    player_details = details_map.get(str(player_id), {"name": f"Игрок #{player_id}"})
                    label = f"ℹ️ {player_details.get('name')}"
                    description = "Уровень: N/A"
                    entities_list.append(
                        InspectedEntityDTO(entity_id=str(player_id), label=label, description=description)
                    )
            else:
                # Логика для NPC и других
                pass

            # --- Шаг 5: Финальное DTO ---
            pagination_info = PaginationInfoDTO(current_page=page, total_pages=total_pages, category_key=category_key)
            title_map = {"players": "Игроки в локации", "npcs": "NPC в локации"}
            
            return InspectionListDTO(
                title=title_map.get(category_key, "Список объектов"),
                entities=entities_list,
                pagination=pagination_info
            )
        except Exception as e:
            self.logger.error(f"Критическая ошибка в ListCategoryHandler: {e}", exc_info=True)
            return None