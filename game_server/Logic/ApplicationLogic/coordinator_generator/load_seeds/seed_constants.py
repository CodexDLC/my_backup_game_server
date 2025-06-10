# game_server/utils/load_seeds/seed_constants.py

FILE_LOAD_ORDER = [
    # 000_system/001_worlds
    '001_worlds.yml',
    '002_regions.yml',
    # 000_system/001_worlds/subregions
    '001_subregions.yml',
    '002_subregions.yml',
    '003_subregions.yml',
    '004_subregions.yml',
    '005_subregions.yml',
    '006_subregions.yml',
    
    # 000_system/002_state_entities/entities
    '001_state_entity.yml',
    '002_state_entity.yml',
    '003_state_entity.yml',
    '004_state_entity.yml',
    '005_state_entity.yml',
    # 000_system/002_state_entities
    'state_entity.yml', 
    
    # character
    'background_story.yml',
    'inventory_rule_generator.yml',
    'personality.yml',
    'skills.yml',
    
    # item (ВАЖНО: Порядок загрузки здесь критичен из-за зависимостей)
    # 1. Modifier_Library (фундаментальная библиотека, на которую ссылаются суффиксы и архетипы)
    'Modifier_Library.yml', # Это тот, что в корне item/
    
    # 2. Материалы (на них ссылаются архетипы)
    # item/Material/ (используем точные названия из вашего дерева)
    '001_Material.yml',
    '002_Material.yml',
    '003_Material.yml',
    '004_Material.yml',
    '005_Material.yml',
    '006_Material.yml',
    
    # 3. Суффиксы (ссылаются на Modifier_Library)
    # item/suffix/ (новая папка с разделенными файлами)
    '001_suffix.yml',
    '002_suffix.yml',
    '003_suffix.yml',
    '004_suffix.yml',
    '005_suffix.yml',

    # creature_type
    '001_creature_type.yml',
    
    # quest
    'discord_quest_description.yml',
    'flag_template.yml',
    'quests.yml',
    'quest_flag.yml',
    'quest_steps.yml',
]