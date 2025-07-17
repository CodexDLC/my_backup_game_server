# game_server/Logic/ApplicationLogic/shared_logic/world_map_service/world_map_builder_utils.py

from typing import List, Dict, Any, Optional
from collections import defaultdict

from game_server.contracts.dtos.orchestrator.data_models import GameLocationData

# 🔥 ИЗМЕНЕНИЕ: Импортируем GameLocationData, так как теперь мы работаем с DTO


class WorldMapBuilderUtils:
    """
    Утилитарные статические методы для построения иерархических структур карты мира.
    """

    @staticmethod
    def build_parent_child_map(locations: List[GameLocationData]) -> Dict[Optional[str], List[GameLocationData]]:
        """
        Строит словарь, где ключ - parent_id, а значение - список дочерних локаций.
        """
        children_by_parent_key = defaultdict(list)
        for loc in locations:
            # 🔥 ИЗМЕНЕНИЕ: Используем loc.parent_id
            if loc.parent_id: # Проверяем, что parent_id не None
                children_by_parent_key[loc.parent_id].append(loc)
            # Если parent_id is None, это корневая локация, у нее нет родителя в этом контексте
        return children_by_parent_key

    @staticmethod
    def get_root_locations(locations: List[GameLocationData]) -> List[GameLocationData]:
        """
        Возвращает список корневых локаций (у которых parent_id is None).
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем loc.parent_id
        return [loc for loc in locations if loc.parent_id is None]

    @staticmethod
    def get_location_by_access_key(locations: List[GameLocationData]) -> Dict[str, GameLocationData]:
        """
        Возвращает словарь локаций, где ключ - access_key локации.
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем loc.access_key
        return {loc.access_key: loc for loc in locations}

    # 🔥 НОВОЕ (или восстановленное, если было удалено): Этот метод может быть полезен,
    # но его не было в предоставленном вами коде. Если он нужен, добавьте его.
    # @staticmethod
    # def get_all_child_access_keys(all_locations: List[GameLocationData]) -> List[str]:
    #     """
    #     Получает все access_key, которые являются дочерними для какой-либо локации.
    #     """
    #     child_keys = set()
    #     for loc in all_locations:
    #         if loc.parent_id:
    #             child_keys.add(loc.access_key)
    #     return list(child_keys)
