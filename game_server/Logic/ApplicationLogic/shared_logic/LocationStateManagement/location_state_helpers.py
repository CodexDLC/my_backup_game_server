# game_server/Logic/ApplicationLogic/shared_logic/LocationStateManagement/location_state_helpers.py

from typing import Dict, Any, Optional
from datetime import datetime
from game_server.contracts.dtos.game_commands.data_models import LocationDynamicSummaryDTO

def extract_summary_from_location_state(location_state: Optional[Dict[str, Any]]) -> LocationDynamicSummaryDTO:
    """
    Вспомогательная функция для извлечения сводных данных из документа состояния локации.

    Args:
        location_state (Optional[Dict[str, Any]]): Документ состояния локации из MongoDB.

    Returns:
        LocationDynamicSummaryDTO: Сводные данные о состоянии локации.
    """
    if not location_state:
        return LocationDynamicSummaryDTO()

    players_count = len(location_state.get("players", []))
    npcs_count = len(location_state.get("npcs", []))

    last_update_obj = location_state.get("last_update")
    last_update_str = ""
    if last_update_obj:
        if isinstance(last_update_obj, Dict) and "$date" in last_update_obj:
            last_update_str = last_update_obj["$date"]
        elif isinstance(last_update_obj, datetime):
            last_update_str = last_update_obj.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    return LocationDynamicSummaryDTO(
        players_in_location=players_count,
        npcs_in_location=npcs_count,
        last_update=last_update_str
    )