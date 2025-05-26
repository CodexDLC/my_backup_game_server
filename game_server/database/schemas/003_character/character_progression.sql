-- Файл: character_progression.sql
-- Система прокачки и начисления опыта

CREATE TABLE IF NOT EXISTS character_skills (
    character_id INTEGER NOT NULL,
    skill_key INTEGER NOT NULL,  -- ✅ Изменен тип с VARCHAR(100) на INTEGER
    level INTEGER DEFAULT 0 NOT NULL,  -- Стартовый уровень теперь 0
    xp BIGINT DEFAULT 0 NOT NULL,
    progress_state VARCHAR(10) DEFAULT 'PLUS' NOT NULL,
    CONSTRAINT character_skills_progress_state_check CHECK (
        progress_state IN ('PLUS', 'PAUSE', 'MINUS')
    )
);

CREATE INDEX idx_character_skills_character_id ON character_skills (character_id);
CREATE INDEX idx_character_skills_skill_key ON character_skills (skill_key);
CREATE INDEX idx_character_skills_compound ON character_skills (character_id, skill_key);
CREATE INDEX idx_character_skills_xp ON character_skills (xp);
CREATE INDEX idx_character_skills_xp_level ON character_skills (xp, level);



CREATE TABLE IF NOT EXISTS character_exploration_chances (
    character_id INTEGER PRIMARY KEY,
    combat_chance FLOAT NOT NULL,
    magic_chance FLOAT NOT NULL,
    gathering_chance FLOAT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exploration_chances ON character_exploration_chances (combat_chance, magic_chance, gathering_chance);
CREATE INDEX idx_last_updated ON character_exploration_chances (last_updated);


CREATE TABLE IF NOT EXISTS xp_tick_data (
    tick_id integer NOT NULL,
    character_id integer,
    skill_id integer,
    xp_generated integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


