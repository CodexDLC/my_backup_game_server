# game_server/app_discord_bot/app/services/game_modules/inspection/inspection_templates.py

from typing import Optional

def get_category_description(category_key: str, count: int) -> Optional[str]:
    """
    Возвращает текстовое описание для указанной категории и количества объектов.
    Это центральное место для всех текстов осмотра.
    """
    if category_key == "players":
        if count == 1:
            return f"Вы видите в тени силуэт **{count}** игрока."
        elif 1 < count < 5:
            return f"Вы видите в тени силуэты **{count}** игроков."
        else:
            return f"Вы видите в тени силуэты **{count}** игроков."
        
    elif category_key == "npcs":
        return f"Неподалеку вы замечаете **{count}** персонажей, с которыми можно поговорить."
        
    elif category_key == "monsters":
        if count == 1:
            return f"Вдалеке слышится рык **{count}** монстра."
        elif 1 < count < 5:
            return f"Рядом бродят **{count}** монстра, будьте осторожны!"
        else:
            return f"Воздух пропитан запахом чудовищ, их здесь **{count}**."

    elif category_key == "battle":
        if count == 1:
            return f"В локации идёт **{count}** боевое столкновение."
        else:
            return f"В локации происходят **{count}** боевые столкновения."

    elif category_key == "chests":
        if count == 1:
            return f"Вы замечаете **{count}** сундук, возможно, он содержит сокровища."
        else:
            return f"В поле зрения попадает **{count}** сундуков."

    elif category_key == "quests":
        if count == 1:
            return f"Вы нашли **{count}** активное задание."
        else:
            return f"В локации доступно **{count}** заданий."
            
    elif category_key == "portals":
        if count == 1:
            return f"Мерцает **{count}** портал, готовый перенести вас."
        else:
            return f"Вы видите **{count}** мерцающих порталов."

    elif category_key == "merchants":
        if count == 1:
            return f"Неподалеку расположился **{count}** торговец."
        else:
            return f"На рынке вы видите **{count}** торговцев."

    elif category_key == "crafting_stations":
        if count == 1:
            return f"Рядом находится **{count}** станция крафта."
        else:
            return f"Вы видите **{count}** станций крафта."
        
    return None