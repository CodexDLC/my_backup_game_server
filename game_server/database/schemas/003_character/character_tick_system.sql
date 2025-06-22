-- 🔹 Таблица активных авто-сессий персонажа
CREATE TABLE IF NOT EXISTS auto_sessions (
    character_id INTEGER PRIMARY KEY,  -- ✅ `character_id` теперь уникальный ключ
    active_category TEXT NOT NULL,
    next_tick_at TIMESTAMPTZ NOT NULL,
    last_tick_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_auto_sessions_next_tick_at ON auto_sessions(next_tick_at);
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
