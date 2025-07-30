# Этот файл собирает все словари описаний из отдельных файлов.

# Импорт словарей для глобальных зон
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.global_zones_descriptions import DESCRIPTIONS_GLOBAL_ZONES

# Импорт словарей для городских кварталов
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.magic_wing_1_10_descriptions import DESCRIPTIONS_MAGIC_WING_1_10
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.academy_center_1_20_descriptions import DESCRIPTIONS_ACADEMY_CENTER_1_20
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.combat_wing_1_30_descriptions import DESCRIPTIONS_COMBAT_WING_1_30
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.western_gates_1_40_descriptions import DESCRIPTIONS_WESTERN_GATES_1_40
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.central_district_1_50_descriptions import DESCRIPTIONS_CENTRAL_DISTRICT_1_50
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.eastern_gates_1_60_descriptions import DESCRIPTIONS_EASTERN_GATES_1_60
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.western_slums_1_70_descriptions import DESCRIPTIONS_WESTERN_SLUMS_1_70
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.port_district_1_80_descriptions import DESCRIPTIONS_PORT_DISTRICT_1_80
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.city.eastern_slums_1_90_descriptions import DESCRIPTIONS_EASTERN_SLUMS_1_90

# Импорт словаря для шлюзов


# Импорт словарей для стен
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.wall.gateways_descriptions import DESCRIPTIONS_GATEWAYS


from game_server.app_discord_bot.config.assets.descriptions_text.world_map.wall.wall_paths_descriptions import DESCRIPTIONS_WALL_SECTIONS
from game_server.app_discord_bot.config.assets.descriptions_text.world_map.wall.wall_tops_descriptions import DESCRIPTIONS_TOWERS


# Объединение всех словарей в один главный словарь LOCATION_DESCRIPTIONS
# Используется оператор слияния словарей (|) для Python 3.9+
LOCATION_DESCRIPTIONS = DESCRIPTIONS_GLOBAL_ZONES | \
                        DESCRIPTIONS_MAGIC_WING_1_10 | \
                        DESCRIPTIONS_ACADEMY_CENTER_1_20 | \
                        DESCRIPTIONS_COMBAT_WING_1_30 | \
                        DESCRIPTIONS_WESTERN_GATES_1_40 | \
                        DESCRIPTIONS_CENTRAL_DISTRICT_1_50 | \
                        DESCRIPTIONS_EASTERN_GATES_1_60 | \
                        DESCRIPTIONS_WESTERN_SLUMS_1_70 | \
                        DESCRIPTIONS_PORT_DISTRICT_1_80 | \
                        DESCRIPTIONS_EASTERN_SLUMS_1_90 | \
                        DESCRIPTIONS_GATEWAYS | \
                        DESCRIPTIONS_WALL_SECTIONS | \
                        DESCRIPTIONS_TOWERS

# Пример использования (для проверки, не для реального кода):
# print(LOCATION_DESCRIPTIONS["2_DESCRIPTION_KEY"]["default"])
# print(LOCATION_DESCRIPTIONS["TOWER_1_KEY"]["default"])