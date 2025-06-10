CREATE TABLE account_info (
    account_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    avatar TEXT,
    locale VARCHAR(10),
    region VARCHAR(20),
    status VARCHAR(20) DEFAULT 'active',
    role VARCHAR(20) DEFAULT 'user',
    twofa_enabled BOOLEAN DEFAULT FALSE,
    linked_platforms JSONB DEFAULT '{}',
    auth_token TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- 🔥 Удалили `ON UPDATE`
);



-- 🔹 Основные параметры родословных персонажей
CREATE TABLE IF NOT EXISTS bloodlines (
    bloodline_id SERIAL PRIMARY KEY,      -- Уникальный ID для каждой линии наследия
    name VARCHAR(100) NOT NULL UNIQUE,    -- Внутреннее название (например, 'Ancestral Warrior', 'Shadow Weaver', 'Starforged Spirit')
    description TEXT,                     -- Скрытое описание для разработчиков/лора (что это за линия)
    --
    -- 👇 Это ключевое поле для скрытых бонусов
    inherent_bonuses JSONB NOT NULL,      -- JSONB: {"stat_modifiers": {"strength": 2, "agility": 1}, "skill_xp_multiplier": {"COMBAT_SKILLS": 1.15}, "passive_abilities": [701, 705]}
                                          -- Модификаторы статов, множители опыта для групп навыков, ссылки на пассивные способности (abilities.ability_id)
    --
    rarity_weight INTEGER DEFAULT 100,    -- Вес для случайного выбора (чем выше, тем чаще встречается, по умолчанию 100)
    story_fragments JSONB                 -- JSONB: {"hidden_lore": ["Часто видят во снах древние битвы", "Необъяснимая тяга к руинам"], "hidden_connections": ["ancient_war", "elemental_magic"]}
                                          -- Фрагменты лора, которые могут быть раскрыты позже в игре
);