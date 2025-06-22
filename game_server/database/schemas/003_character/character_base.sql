
-- 🔹 Основная таблица персонажей
CREATE TABLE IF NOT EXISTS characters (
    character_id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    surname VARCHAR(100),
    bloodline_id INTEGER,
    creature_type_id INTEGER NOT NULL,
    personality_id INTEGER,          -- ✅ ДОБАВЛЕНО
    background_story_id INTEGER,     -- ✅ ДОБАВЛЕНО
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT false NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'offline',

    CONSTRAINT fk_account FOREIGN KEY (account_id) REFERENCES account_info(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_bloodline FOREIGN KEY (bloodline_id) REFERENCES bloodlines(bloodline_id) ON DELETE SET NULL,
    CONSTRAINT fk_creature_type FOREIGN KEY (creature_type_id) REFERENCES creature_types(creature_type_id) ON DELETE RESTRICT,
    CONSTRAINT fk_personality FOREIGN KEY (personality_id) REFERENCES personalities(personality_id) ON DELETE SET NULL, -- ✅ ДОБАВЛЕНО
    CONSTRAINT fk_background_story FOREIGN KEY (background_story_id) REFERENCES background_stories(story_id) ON DELETE SET NULL -- ✅ ДОБАВЛЕНО
);



-- 🔹 Таблица характеристик персонажа
CREATE TABLE IF NOT EXISTS characters_special (
    character_id INTEGER PRIMARY KEY,  -- Добавили главный ключ
    strength INTEGER,
    perception INTEGER,
    endurance INTEGER,
    agility INTEGER,
    intelligence INTEGER,
    charisma INTEGER,
    luck INTEGER,
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE  -- Добавили связь
);


-- Таблица: character_skills
CREATE TABLE IF NOT EXISTS character_skills (
    character_id INTEGER NOT NULL,
    skill_key VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 0 NOT NULL,
    xp BIGINT DEFAULT 0 NOT NULL,
    progress_state VARCHAR(10) DEFAULT 'PAUSE' NOT NULL,
    -- player_max_level_override INTEGER, -- ✅ УДАЛЕНО: Соответствует модели, где этого поля нет
    
    CONSTRAINT character_skills_progress_state_check CHECK (
        progress_state IN ('PLUS', 'PAUSE', 'MINUS')
    ),
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE,
    CONSTRAINT fk_skill FOREIGN KEY (skill_key) REFERENCES skills(skill_key) ON DELETE CASCADE,
    PRIMARY KEY (character_id, skill_key)
);