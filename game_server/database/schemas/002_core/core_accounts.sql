-- Файл: core_accounts.sql
-- Управление пользователями и их данными

CREATE TABLE IF NOT EXISTS account_info (
    account_id INTEGER PRIMARY KEY DEFAULT nextval('account_info_account_id_seq'),  -- Используем последовательность для целочисленного ID
    username VARCHAR(50) NOT NULL,
    email TEXT,
    password_hash TEXT,
    google_id TEXT,
    discord_id TEXT,
    telegram_id TEXT,
    twitter_id TEXT,
    steam_id TEXT,
    twitch_id TEXT,
    game_id INTEGER,
    platform VARCHAR(50) DEFAULT 'website' NOT NULL,
    linked_platforms TEXT,
    auth_token TEXT,
    avatar TEXT,
    locale TEXT,
    region TEXT,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    twofa_enabled BOOLEAN DEFAULT false NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITHOUT TIME ZONE,
    UNIQUE (discord_id),
    UNIQUE (email),
    UNIQUE (game_id),
    UNIQUE (google_id),
    UNIQUE (steam_id),
    UNIQUE (telegram_id),
    UNIQUE (twitch_id),
    UNIQUE (twitter_id),
    UNIQUE (username)
);


