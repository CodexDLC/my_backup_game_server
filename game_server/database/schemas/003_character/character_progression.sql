-- 🔹 Система прокачки и навыков


-- 🔹 Улучшение исследования персонажа
CREATE TABLE IF NOT EXISTS character_exploration_chances (
    character_id INTEGER PRIMARY KEY, -- ✅ Уникальный `character_id`
    combat_chance FLOAT NOT NULL,
    magic_chance FLOAT NOT NULL,
    gathering_chance FLOAT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 🔹 Записи начисленного XP
CREATE TABLE IF NOT EXISTS xp_tick_data (
    tick_id SERIAL PRIMARY KEY, -- ✅ Уникальный идентификатор
    character_id INTEGER,
    skill_id INTEGER,
    xp_generated INTEGER,
    "timestamp" TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
