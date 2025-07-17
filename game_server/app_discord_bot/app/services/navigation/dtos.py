# game_server/app_discord_bot/app/services/navigation/dtos.py

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class NavigationDisplayDataDTO:
    """
    DTO для передачи данных о локации от логического слоя к презентационному
    для отображения навигационного интерфейса.
    """
    location_name: str = field(metadata={"description": "Название текущей локации."})
    location_description: str = field(metadata={"description": "Описание текущей локации."})
    unified_display_type: str = field(metadata={"description": "Унифицированный тип отображения локации (например, HUB_LOCATION, INTERNAL_LOCATION)."})
    current_location_id: str = field(metadata={"description": "ID текущей локации."})
    exits: List[Dict[str, Any]] = field(default_factory=list, metadata={"description": "Список доступных выходов из локации (для формирования кнопок или полей)."})
    image_url: Optional[str] = field(default=None, metadata={"description": "URL изображения локации, если есть."})
    
    # Новое поле для данных полей эмбеда (Fields)
    location_fields_data: List[Dict[str, Any]] = field(default_factory=list, metadata={"description": "Данные для полей эмбеда (name, value, inline)."})
    
    # Поле для данных амбиентного футера
    ambient_footer_data: Dict[str, Any] = field(default_factory=dict, metadata={"description": "Данные для динамического футера основного эмбеда."})
    
    type: str = field(default="LOCATION_DISPLAY", metadata={"description": "Тип DTO для маршрутизации в оркестраторе."})

    def format_ambient_footer_text(self) -> str:
        """
        Форматирует данные для футера основного эмбеда.
        Если данных нет, возвращает заглушку.
        """
        if not self.ambient_footer_data:
            return "Игроков в локации: 0" # Заглушка, если данных нет или они пусты

        parts = []
        players = self.ambient_footer_data.get("players_in_location")
        if players is not None:
            parts.append(f"Игроков в локации: {players}")
        
        npcs = self.ambient_footer_data.get("npcs_in_location")
        if npcs is not None:
            parts.append(f"NPC в локации: {npcs}")
        
        # Можно добавить другие динамические данные
        
        if not parts:
            return "Игроков в локации: 0" # Fallback, если данные есть, но не распознаны
        
        return " | ".join(parts)