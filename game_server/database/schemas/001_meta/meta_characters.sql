-- Файл: meta_characters.sql
-- Основные параметры рас и родословных персонажей

CREATE TABLE public.bloodlines (
    bloodline_id integer NOT NULL,
    bloodline_name character varying(100) DEFAULT 'human'::character varying NOT NULL
);

CREATE TABLE public.races (
    race_id integer NOT NULL,
    name character varying(100) DEFAULT ''::character varying NOT NULL,
    founder_id integer DEFAULT 0 NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);
