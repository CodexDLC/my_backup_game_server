-- Файл: character_base.sql
-- Основные атрибуты и данные персонажа

CREATE TABLE IF NOT EXISTS characters (
    character_id integer NOT NULL PRIMARY KEY,  -- Оставляем integer для character_id
    account_id integer NOT NULL,  -- Идентификатор аккаунта
    name character varying(255) NOT NULL,  -- Имя персонажа
    surname character varying(100),  -- Фамилия персонажа
    bloodline_id integer,  -- Идентификатор рода
    race_id integer DEFAULT 1 NOT NULL,  -- Идентификатор расы (например, человек)
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,  -- Время создания
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,  -- Время обновления
    is_deleted boolean DEFAULT false NOT NULL,  -- Флаг удаления персонажа
    CONSTRAINT unique_account UNIQUE(account_id)  -- Добавляем уникальность для account_id
);


CREATE TABLE IF NOT EXISTS characters_special (
    character_id integer NOT NULL,
    strength integer,
    perception integer,
    endurance integer,
    agility integer,
    intelligence integer,
    charisma integer,
    luck integer
);
