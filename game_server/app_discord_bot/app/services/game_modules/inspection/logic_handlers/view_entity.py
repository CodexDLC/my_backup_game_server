# game_server/app_discord_bot/app/services/game_modules/inspection/logic_handlers/view_entity.py

import discord
import inject
import logging
from typing import Dict, Any, Optional, List

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_utils.action_providers import ACTION_PROVIDERS

from ..inspection_dtos import EntityDetailsDTO, ActionDTO
# Импортируем реестр поставщиков



class ViewEntityHandler:
    """
    Обрабатывает команду 'action:view_details:<entity_id>'.
    Действует как диспетчер: получает данные и передает их соответствующему
    поставщику действий (Action Provider) для получения списка кнопок.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    def _get_mock_entity_details(self, entity_id: str, category_key: str) -> Dict[str, Any]:
        """
        ЗАГЛУШКА: Имитирует запрос к бэкенду.
        """
        self.logger.info(f"[ЗАГЛУШКА] Запрос деталей для сущности ID: '{entity_id}', Категория: '{category_key}'")

        mock_details_data = {
            "player_1": {
                "entity_id": "player_1", "name": "Shadow", "level": 15, "hp": "100/100", "mana": "50/50",
                "class": "Воин", "location": "Таверна 'Усталый Путник'", "last_online": "5 минут назад",
                "is_friend": True, "image_url": "https://placehold.co/128x128/000000/FFFFFF?text=Shadow",
                "description": "Могучий воин, известный своей скрытностью и силой в бою."
            },
            "npc_neutral_1": {
                "entity_id": "npc_neutral_1", "name": "Торговец Боб", "type": "Торговец", "wares_count": 25,
                "location": "Рыночная площадь", "image_url": "https://placehold.co/128x128/00FF00/000000?text=Bob",
                "description": "Веселый торговец, предлагающий широкий ассортимент товаров."
            },
            "npc_enemy_1": {
                "entity_id": "npc_enemy_1", "name": "Гоблин-разведчик", "level": 5, "hp": "50/50", 
                "type": "Гоблин", "weakness": "Огонь", "location": "Лес Теней",
                "image_url": "https://placehold.co/128x128/FF0000/FFFFFF?text=Goblin",
                "description": "Маленький, но проворный гоблин."
            },
            "chest_1": {
                "entity_id": "chest_1", "name": "Деревянный сундук", "status": "Закрыт",
                "contents_hint": "Содержит обычные припасы.", "image_url": "https://placehold.co/128x128/8B4513/FFFFFF?text=Chest",
                "description": "Старый деревянный сундук."
            }
        }
        return mock_details_data.get(entity_id, {"name": "Неизвестно"})

    async def execute(self, command_str: str, interaction: discord.Interaction) -> Optional[EntityDetailsDTO]:
        """
        Основной метод выполнения логики.
        """
        self.logger.info(f"Обработка команды '{command_str}' для пользователя {interaction.user.id}")

        # --- Шаг 1: Парсинг команды ---
        parts = command_str.split(':')
        if len(parts) < 3: return None
        entity_id = parts[2]

        # --- Шаг 2: Получение данных и категории (ОБНОВЛЕННАЯ ЛОГИКА) ---
        category_key_from_id = "unknown"
        if entity_id.startswith("player_"):
            category_key_from_id = "players"
        elif entity_id.startswith("npc_neutral_"):
            category_key_from_id = "npc_neutral"
        elif entity_id.startswith("npc_enemy_"):
            category_key_from_id = "npc_enemy"
        elif entity_id.startswith("chest_"):
            category_key_from_id = "chests"
        
        details_data = self._get_mock_entity_details(entity_id, category_key_from_id)

        # --- Шаг 3: Формирование полей для Embed (ОБНОВЛЕННАЯ ЛОГИКА) ---
        fields_list = []
        if category_key_from_id == "players":
            fields_list.append({"name": "Уровень", "value": details_data.get("level", "N/A"), "inline": True})
            fields_list.append({"name": "HP", "value": details_data.get("hp", "N/A"), "inline": True})
            fields_list.append({"name": "Мана", "value": details_data.get("mana", "N/A"), "inline": True})
            fields_list.append({"name": "Класс", "value": details_data.get("class", "N/A"), "inline": True})
        elif category_key_from_id == "npc_neutral":
            fields_list.append({"name": "Тип", "value": details_data.get("type", "N/A"), "inline": True})
            fields_list.append({"name": "Локация", "value": details_data.get("location", "N/A"), "inline": True})
        elif category_key_from_id == "npc_enemy":
            fields_list.append({"name": "Уровень", "value": details_data.get("level", "N/A"), "inline": True})
            fields_list.append({"name": "HP", "value": details_data.get("hp", "N/A"), "inline": True})
            fields_list.append({"name": "Тип", "value": details_data.get("type", "N/A"), "inline": True})
        
        # --- Шаг 4: Получение кнопок от Поставщика ---
        actions_for_entity: List[ActionDTO] = []
        provider_func = ACTION_PROVIDERS.get(category_key_from_id)
        
        if provider_func:
            actions_for_entity = provider_func(details_data, interaction.user.id)
        else:
            self.logger.warning(f"Не найден поставщик действий для категории '{category_key_from_id}'")

        # --- Шаг 5: Создание и возврат финального DTO ---
        return EntityDetailsDTO(
            entity_id=entity_id,
            category_key=category_key_from_id,
            title=f"Детали: {details_data.get('name', 'Неизвестно')}",
            description=details_data.get("description", "Нет подробного описания."),
            fields=fields_list,
            image_url=details_data.get("image_url"),
            actions=actions_for_entity
        )