-- Файл: character_progression.sql
-- Система прокачки и начисления опыта

CREATE TABLE public.character_skills (
    character_id integer NOT NULL,
    skill_id integer NOT NULL,
    level integer DEFAULT 1 NOT NULL,
    xp bigint DEFAULT 0 NOT NULL,
    progress_state character varying(10) DEFAULT 'PLUS'::character varying NOT NULL,
    CONSTRAINT character_skills_progress_state_check CHECK (((progress_state)::text = ANY ((ARRAY['PLUS'::character varying, 'PAUSE'::character varying, 'MINUS'::character varying])::text[])))
);

CREATE TABLE public.xp_tick_data (
    tick_id integer NOT NULL,
    character_id integer,
    skill_id integer,
    xp_generated integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


