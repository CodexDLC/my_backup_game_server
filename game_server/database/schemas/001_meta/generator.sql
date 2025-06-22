
CREATE TABLE creature_types (

    creature_type_id INTEGER PRIMARY KEY,

    name VARCHAR(100) NOT NULL,

    description TEXT NOT NULL,

    category VARCHAR(50) NOT NULL,

    subcategory VARCHAR(100), -- NULLABLE по умолчанию в SQL, можно явно указать NULL

    visual_tags JSONB,         -- NULLABLE по умолчанию в SQL, можно явно указать NULL

    rarity_weight INTEGER DEFAULT 100,

    is_playable BOOLEAN DEFAULT FALSE

);


CREATE TABLE IF NOT EXISTS background_stories (
    story_id SERIAL PRIMARY KEY,              -- Уникальный ID для каждой предыстории
    name VARCHAR(100) NOT NULL UNIQUE,        -- Внутреннее название (например, 'Orphaned_Street_Thief', 'Apprentice_Alchemist', 'Desert_Nomad')
    display_name VARCHAR(100) NOT NULL,       -- Отображаемое название (если нужно будет показывать игроку, например, "Уличный вор-сирота")
    short_description TEXT,                   -- Краткое описание для разработчиков/лора
    
    -- Влияние на генерацию персонажа
    stat_modifiers JSONB,                     -- JSONB: {"strength": 1, "agility": 1} - Небольшие бонусы к статам
    skill_affinities JSONB,                   -- JSONB: {"SNEAK": 0.15, "LOCKPICKING": 0.1} - Склонность к конкретным навыкам или группам навыков (тегам)
    initial_inventory_items JSONB,            -- JSONB: {"item_id_1": 1, "item_id_2": 3} - Начальные предметы (ссылки на IDs предметов и количество)
    starting_location_tags JSONB,             -- JSONB: ["urban", "slums"] - Предпочтительные теги для стартовой локации (для более сложного генератора мира)
    
    -- Лор и сюжетные элементы
    lore_fragments JSONB,                     -- JSONB: ["Потерял семью в юном возрасте", "Имеет долг перед гильдией"] - Фрагменты лора для развития истории
    potential_factions JSONB,                 -- JSONB: ["thieves_guild", "beggars_union"] - Потенциальные фракции, с которыми связана предыстория
    
    rarity_weight INTEGER DEFAULT 100         -- Вес для случайного выбора при генерации (чем выше, тем чаще встречается)
);

CREATE TABLE IF NOT EXISTS personalities (
    personality_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,     -- Название личности
    description TEXT,                      -- Подробное описание этой личности (для разработчика)
    personality_group VARCHAR(50),         -- ✅ НОВОЕ: Широкая категория личности (например, 'Moral', 'Combat-Oriented')
    behavior_tags JSONB,                   -- Набор тегов, описывающих поведение (["greedy", "social_avoidant"])
    dialogue_modifiers JSONB,              -- Модификаторы для диалоговой системы
    combat_ai_directives JSONB,            -- Директивы для боевого ИИ
    quest_interaction_preferences JSONB,   -- Предпочтения при взаимодействии с квестами/NPC
    trait_associations JSONB,              -- ✅ НОВОЕ: Ассоциации/исключения с другими чертами/особенностями (JSONB)
    applicable_game_roles JSONB,           -- Список game_role из creature_types, к которым применима эта личность
    rarity_weight INTEGER DEFAULT 100,     -- Вес для случайного выбора при генерации
    ai_priority_level INTEGER DEFAULT 50   -- ✅ НОВОЕ: Насколько сильно эта личность влияет на AI (1-100)
);



CREATE TABLE IF NOT EXISTS character_pool (
    character_pool_id SERIAL PRIMARY KEY,      -- Уникальный ID для сущности в пуле

    -- Ссылки на справочники, определяющие тип и базовые свойства
    creature_type_id INTEGER NOT NULL,         -- Ссылка на creature_types (ТОЛЬКО те, где is_playable = TRUE)
    gender VARCHAR(20) NOT NULL,               -- Пол персонажа ('male', 'female', etc.)

    -- Изначальная роль NPC, определенная на основе сгенерированных статов
    base_stats JSONB NOT NULL,                 -- JSONB: Базовые значения STR, AGI, INT, etc. (сгенерированные)
    initial_role_name VARCHAR(100) NOT NULL,   -- 🔥🔥🔥 ИЗМЕНЕНО: теперь NOT NULL, как мы договорились
    initial_skill_levels JSONB NOT NULL,       -- JSONB: Начальные уровни навыков (сгенерированные на основе роли)

    -- Основные атрибуты (уже сгенерированные значения)
    name VARCHAR(255) NOT NULL,                -- Уже сгенерированное имя
    surname VARCHAR(100),                      -- Уже сгенерированная фамилия
    personality_id INTEGER,                    -- Ссылка на personalities
    background_story_id INTEGER,               -- Ссылка на background_stories
   
    visual_appearance_data JSONB,              -- JSONB: Данные о внешнем виде (может быть NULL)

    -- Статус и метаданные пула
    status VARCHAR(50) NOT NULL DEFAULT 'available', -- Статус персонажа в пуле
    is_unique BOOLEAN NOT NULL DEFAULT FALSE,  -- Является ли персонаж уникальным
    rarity_score INTEGER NOT NULL DEFAULT 100, -- Рейтинг редкости (более высокий - более редкий)
    
    -- Временные метки с учетом часового пояса
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Когда был сгенерирован
    last_used_at TIMESTAMP WITH TIME ZONE,     -- Когда был последний раз выдан/использован (для очистки пула)
    death_timestamp TIMESTAMP WITH TIME ZONE   -- Когда персонаж был "удален" из активного пула (умер, поглощен)

    -- 🔥🔥🔥 ВАЖНО: Добавьте или убедитесь в наличии этих внешних ключей,
    -- если они не были добавлены в самой DDL таблице, а только через Alembic.
    -- Это для полноты DDL-скрипта.
    -- FOREIGN KEY (creature_type_id) REFERENCES creature_types(creature_type_id) ON DELETE RESTRICT,
    -- FOREIGN KEY (bloodline_id) REFERENCES bloodlines(bloodline_id) ON DELETE SET NULL,
    -- FOREIGN KEY (personality_id) REFERENCES personalities(personality_id) ON DELETE SET NULL,
    -- FOREIGN KEY (background_story_id) REFERENCES background_stories(story_id) ON DELETE SET NULL
);

-- 🔥🔥 ДОБАВЬТЕ ЭТИ ИНДЕКСЫ, ЕСЛИ ОНИ НЕ БЫЛИ ВЫШЕ В ОСНОВНОЙ DDL
-- Index('idx_character_pool_status', 'status'),
-- Index('idx_character_pool_creature_type', 'creature_type_id'),
-- Index('idx_character_pool_rarity_score', 'rarity_score'),

CREATE TABLE IF NOT EXISTS character_starter_inventories (
    inventory_id SERIAL PRIMARY KEY,        -- Уникальный ID стартового набора
    name VARCHAR(100) NOT NULL UNIQUE,      -- Внутреннее имя набора (например, "Warrior_Basic_Set", "Mage_Elite_Gear")
    description TEXT,                       -- Описание набора
    items JSONB NOT NULL                    -- JSONB, описывающий предметы и их количество в наборе.
                                            -- Пример: {"item_id_1": 1, "item_id_2": 3, "gold": 100}
                                            -- Или более сложная структура, если предметы имеют вариативность.
);


CREATE TABLE IF NOT EXISTS character_inventory_rules (
    rule_id SERIAL PRIMARY KEY,
    quality_level VARCHAR(100) NOT NULL,    -- Уровень качества (например, "STANDARD_QUALITY")
    role_name VARCHAR(100),                 -- Роль (например, "WARRIOR"), может быть NULL для общих правил
    inventory_id INTEGER NOT NULL,          -- ID стартового набора из character_starter_inventories
    -- Можно добавить веса или другие условия
    weight INTEGER DEFAULT 100,

    CONSTRAINT fk_inventory_rule_inventory FOREIGN KEY (inventory_id) REFERENCES character_starter_inventories(inventory_id) ON DELETE CASCADE,
    UNIQUE (quality_level, role_name, inventory_id) -- Обеспечить уникальность правил (если нужно)
);


-- Таблица: inventory_rule_generator
CREATE TABLE IF NOT EXISTS inventory_rule_generator (
    rule_key VARCHAR(150) PRIMARY KEY, -- ✅ ИЗМЕНЕНО: rule_key теперь PRIMARY KEY (соответствует модели)
    rule_id INTEGER NOT NULL UNIQUE,   -- ✅ ИЗМЕНЕНО: rule_id теперь просто UNIQUE (соответствует модели Identity)
    description TEXT,
    quality_level INTEGER NOT NULL,
    weight INTEGER NOT NULL DEFAULT 100,
    activation_conditions JSONB NOT NULL,
    generation_rules JSONB NOT NULL
);

-- Обычный B-Tree индекс для быстрого поиска по уровню качества
CREATE INDEX IF NOT EXISTS idx_inventory_rule_generator_quality_level
ON inventory_rule_generator(quality_level);

-- Специальный GIN-индекс для быстрого поиска внутри JSON-поля с условиями
CREATE INDEX IF NOT EXISTS idx_inventory_rule_generator_activation_conditions_gin
ON inventory_rule_generator USING GIN(activation_conditions);


CREATE TABLE IF NOT EXISTS used_characters_archive (
    archive_id SERIAL PRIMARY KEY,
    original_pool_id INTEGER NOT NULL UNIQUE,     -- ID из таблицы character_pool
    
    -- УНИВЕРСАЛЬНЫЕ ПОЛЯ
    linked_entity_id INTEGER NOT NULL,            -- ID сущности, которой выдан шаблон (игрок, NPC, компаньон)
    activation_type VARCHAR(50) NOT NULL,         -- Тип активации: 'PLAYER', 'NPC_COMPANION', 'NPC_ENEMY', etc.
    
    -- Статус жизненного цикла
    lifecycle_status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'DEAD', 'INACTIVE', 'DESTROYED'
    
    -- Опциональные данные
    linked_account_id INTEGER,                    -- ID аккаунта, если это персонаж игрока (NULL для NPC)
    simplified_pool_data JSONB,                   -- JSON с некритичными данными из пула для истории
    
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);