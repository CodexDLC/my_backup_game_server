# game_server/app_discord_bot/app/services/game_modules/inspection/action_providers.py

from typing import List, Dict, Any

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import ActionDTO
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_utils.entity_actions_config import CHEST_STATE_ACTIONS, NPC_ENEMY_ACTIONS, NPC_NEUTRAL_SUBTYPE_ACTIONS


# --- Функции-поставщики ---

def get_player_actions(details_data: Dict[str, Any], observer_id: int) -> List[ActionDTO]:
    """
    Возвращает список динамических действий для сущности 'Игрок'.
    """
    actions = []
    is_friend = details_data.get("is_friend", False)
    
    if is_friend:
        actions.append(ActionDTO(
            key="remove_friend", 
            label="Удалить из друзей", 
            style="danger", 
            disabled=False,
            custom_id_template="social:remove_friend:{entity_id}"
        ))
    else:
        actions.append(ActionDTO(
            key="add_friend", 
            label="Добавить в друзья", 
            style="primary", 
            disabled=False,
            custom_id_template="social:add_friend:{entity_id}"
        ))
    return actions

def get_npc_neutral_actions(details_data: Dict[str, Any], observer_id: int) -> List[ActionDTO]:
    """
    Возвращает список динамических действий для НЕЙТРАЛЬНЫХ NPC.
    """
    actions = []
    npc_subtype = details_data.get("type")
    action_templates = NPC_NEUTRAL_SUBTYPE_ACTIONS.get(npc_subtype, [])
    
    for template in action_templates:
        actions.append(ActionDTO(
            key=template["key"],
            label=template["label"],
            style=template["style"],
            disabled=False,
            custom_id_template=template.get("custom_id_template")
        ))
    return actions

def get_npc_enemy_actions(details_data: Dict[str, Any], observer_id: int) -> List[ActionDTO]:
    """
    Возвращает список динамических действий для ВРАЖДЕБНЫХ NPC.
    """
    actions = []
    # У врагов пока нет подтипов, используем ключ 'default'
    action_templates = NPC_ENEMY_ACTIONS.get("default", [])
    
    for template in action_templates:
        actions.append(ActionDTO(
            key=template["key"],
            label=template["label"],
            style=template["style"],
            disabled=False,
            custom_id_template=template.get("custom_id_template")
        ))
    return actions


def get_chest_actions(details_data: Dict[str, Any], observer_id: int) -> List[ActionDTO]:
    """
    Возвращает список динамических действий для сущности 'Сундук'.
    """
    actions = []
    chest_state = details_data.get("status")
    action_templates = CHEST_STATE_ACTIONS.get(chest_state, [])

    for template in action_templates:
        actions.append(ActionDTO(
            key=template["key"],
            label=template["label"],
            style=template["style"],
            disabled=False,
            custom_id_template=template.get("custom_id_template")
        ))
    return actions

# --- РЕЕСТР ПОСТАВЩИКОВ (обновленный) ---
ACTION_PROVIDERS = {
    "players": get_player_actions,
    "npc_neutral": get_npc_neutral_actions,
    "npc_enemy": get_npc_enemy_actions,
    "chests": get_chest_actions,
}