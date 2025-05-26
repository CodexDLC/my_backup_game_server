-- Файл: meta_quests.sql
-- Список квестов, не связанных с генератором

CREATE TABLE IF NOT EXISTS quests (
    quest_id integer NOT NULL,
    quest_key integer NOT NULL,
    quest_name character varying(255) NOT NULL,
    description_key character varying(100) NOT NULL,
    reward_key character varying(100) NOT NULL,
    progress_flag character varying(255) DEFAULT NULL::character varying,
    status character varying(50) DEFAULT 'inactive'::character varying NOT NULL
);

CREATE TABLE IF NOT EXISTS quest_steps (
    step_key character varying(100) NOT NULL,
    quest_key integer NOT NULL,
    step_order integer NOT NULL,
    description_key character varying(100) NOT NULL,
    visibility_condition character varying(255),
    reward_key character varying(100),
    status character varying(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS quest_flags (
    flag_id integer NOT NULL,
    flag_key character varying(100) NOT NULL,
    quest_key integer,
    step_key character varying(100),
    flag_key_template character varying(100),
    value text NOT NULL
);