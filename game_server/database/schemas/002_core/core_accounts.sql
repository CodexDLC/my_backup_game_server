-- Файл: core_accounts.sql
-- Управление пользователями и их данными

CREATE TABLE public.account_info (
    account_id integer NOT NULL,
    username character varying(50),
    email text,
    password_hash text,
    google_id text,
    discord_id text,
    telegram_id text,
    twitter_id text,
    steam_id text,
    twitch_id text,
    game_id integer,
    platform character varying(50) DEFAULT 'website'::character varying NOT NULL,
    linked_platforms text,
    auth_token text,
    avatar text,
    locale text,
    region text,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    role character varying(20) DEFAULT 'user'::character varying NOT NULL,
    twofa_enabled boolean DEFAULT false NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login timestamp without time zone
);

