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

-- Таблица: account_game_data
-- Хранит игровые данные, связанные с аккаунтом, влияющие на всех персонажей.
CREATE TABLE IF NOT EXISTS account_game_data (
    account_id INTEGER PRIMARY KEY, -- Ссылка на account_info.account_id (один-к-одному)
    past_life_fragment_id INTEGER,  -- Ссылка на past_life_fragments.fragment_id
    
    -- JSON-поле для хранения информации о персонажах аккаунта в игровом контексте
    -- Возможно, список character_id или краткие сведения о них
    characters_json JSONB DEFAULT '[]'::jsonb, 
    
    -- JSON-поле для данных системы карт
    account_cards_data JSONB DEFAULT '{}'::jsonb,
    
    -- Привязка к шарду/серверу
    shard_id VARCHAR(50), -- Идентификатор шарда, на котором играет аккаунт
    
    -- Временные метки
    last_login_game TIMESTAMP WITH TIME ZONE,
    total_playtime_seconds BIGINT DEFAULT 0,

    CONSTRAINT fk_account_game_data_account_id FOREIGN KEY (account_id) REFERENCES account_info(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_account_game_data_past_life_fragment_id FOREIGN KEY (past_life_fragment_id) REFERENCES past_life_fragments(fragment_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_account_game_data_shard_id ON account_game_data (shard_id);



-- 🔹 Основные параметры родословных персонажей
CREATE TABLE IF NOT EXISTS past_life_fragments (
    fragment_key VARCHAR(100) PRIMARY KEY, -- ✅ ИЗМЕНЕНО: Строковый ключ как PRIMARY KEY
    name VARCHAR(100) NOT NULL UNIQUE,     -- Внутреннее название
    description TEXT,                      -- Скрытое описание
    inherent_bonuses JSONB NOT NULL,       -- JSONB: Наследуемые бонусы
    rarity_weight INTEGER DEFAULT 100,     -- Вес для случайного выбора
    story_fragments JSONB                  -- JSONB: Фрагменты лора
);



-- Таблица: bloodlines_clan
-- Хранит информацию о кланах / организациях игроков
CREATE TABLE IF NOT EXISTS bloodlines_clan (
    clan_id SERIAL PRIMARY KEY,                        -- Уникальный ID клана
    clan_name VARCHAR(100) NOT NULL UNIQUE,            -- Название клана
    description TEXT,                                  -- Описание клана
    leader_account_id INTEGER,                         -- Ссылка на account_info.account_id (лидер клана)
    founding_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- Дата основания
    status VARCHAR(50) DEFAULT 'active',               -- Статус клана (active, dissolved, pending, etc.)
    member_count INTEGER DEFAULT 0,                    -- Текущее количество участников
    reputation BIGINT DEFAULT 0,                       -- Репутация клана
    assets_json JSONB DEFAULT '{}'::jsonb,             -- Активы клана (сокровищница и т.п.)
    policies_json JSONB DEFAULT '{}'::jsonb,           -- Правила клана, членство и т.п.
    
    CONSTRAINT fk_clan_leader FOREIGN KEY (leader_account_id) REFERENCES account_info(account_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_clan_leader_account_id ON bloodlines_clan (leader_account_id);
CREATE INDEX IF NOT EXISTS idx_clan_status ON bloodlines_clan (status);