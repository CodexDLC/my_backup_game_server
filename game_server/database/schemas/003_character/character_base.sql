-- Файл: character_base.sql
-- Основные атрибуты и данные персонажа

CREATE TABLE public.characters (
    character_id integer NOT NULL,
    account_id integer,
    name character varying(255) NOT NULL,
    surname character varying(100),
    bloodline_id integer,
    race_id integer DEFAULT 1 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false NOT NULL
);

CREATE TABLE public.characters_special (
    character_id integer NOT NULL,
    strength integer,
    perception integer,
    endurance integer,
    agility integer,
    intelligence integer,
    charisma integer,
    luck integer
);
