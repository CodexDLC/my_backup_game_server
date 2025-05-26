-- Файл: meta_characters.sql
-- Основные параметры рас и родословных персонажей

CREATE TABLE IF NOT EXISTS bloodlines (
    bloodline_id integer NOT NULL,
    bloodline_name character varying(100) DEFAULT 'human'::character varying NOT NULL
);

CREATE TABLE IF NOT EXISTS races (
    race_id integer NOT NULL,
    name character varying(100) DEFAULT ''::character varying NOT NULL,
    founder_id integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
