from typing import List, Dict, Any, Optional
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_generator import CREATURE_TYPE_CATEGORY_RACE
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_creature_type_manager import CreatureTypeManager

# Предполагаемые импорты констант из вашего проекта:
# from game_server.Logic.InfrastructureLogic.Generators.coordinator_generator.constant.constant_generator import PLAYABLE_CATEGORIES, MIN_RARITY_FOR_PLAYABLE
# from game_server.Logic.InfrastructureLogic.Generators.coordinator_generator.generator_settings import DEFAULT_PLAYER_START_LEVEL

async def process_playable_character_races(
    all_raw_types: List[Dict[str, Any]],
    types_by_category_map: Dict[str, List[Dict[str, Any]]],
    creature_type_manager: CreatureTypeManager # Для потенциальной загрузки initial_skills
) -> List[Dict[str, Any]]:
    """
    Обрабатывает сырые данные типов существ для создания списка игровых рас.
    Формирует список словарей, каждый из которых содержит:
    creature_type_id, race_key, name, description, visual_tags и rarity_weight.
    """
    race_types_list = []
    
    # Получаем все типы существ с категорией "РАСА" из кэша оркестратора
    potential_races = types_by_category_map.get(CREATURE_TYPE_CATEGORY_RACE, []) 

    for ct_data in potential_races:
        # Фильтруем только те, что являются игровыми (is_playable=True)
        if ct_data.get("is_playable"): 
            # Формируем словарь с требуемыми полями для генератора
            race_info = {
                "creature_type_id": ct_data["creature_type_id"],
                "race_key": ct_data.get("subcategory"), # subcategory превращается в race_key
                "name": ct_data["name"],               # Отображаемое имя расы
                "description": ct_data["description"], # Описание расы
                "visual_tags": ct_data.get("visual_tags", {}), # JSONB, может быть пустым словарем
                "rarity_weight": ct_data.get("rarity_weight", 100) # ДОБАВЛЕНО: rarity_weight с дефолтом 100
            }
            
            # На данный момент не подгружаем initial_skills, так как это не требовалось
            # для *выбора* расы. Если потребуется, этот блок можно будет добавить.
            
            race_types_list.append(race_info)
            
    return race_types_list