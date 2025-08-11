# Этот файл собирает все словари описаний из отдельных файлов.

# Импорт словарей для стен
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.wall.wall_paths_descriptions import DESCRIPTIONS_WALL_SECTIONS
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.wall.wall_tops_descriptions import DESCRIPTIONS_TOWERS


# Объединение всех словарей в один главный словарь LOCATION_DESCRIPTIONS
# с вложенной структурой.
LOCATION_DESCRIPTIONS = {
    "wall_paths": DESCRIPTIONS_WALL_SECTIONS,
    "towers": DESCRIPTIONS_TOWERS
}

# Пример использования:
# print(LOCATION_DESCRIPTIONS["towers"]["1-95_TOWER_01"]["default"])
# print(LOCATION_DESCRIPTIONS["wall_paths"]["1-95_PATH_01-04_1"]["С"])