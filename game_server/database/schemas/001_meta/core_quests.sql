-- Файл: core_quests.sql
-- Полная структура генератора квестов, их типов, условий и наград

-- 🔹 Главный шаблон квестов
CREATE TABLE IF NOT EXISTS quest_templates_master (
    template_id integer NOT NULL,
    template_key character varying(100) NOT NULL,
    type_key character varying(100),
    condition_key character varying(100),
    requirement_key character varying(100),
    reward_key character varying(100)
);

-- 🔹 Категории квестов
CREATE TABLE IF NOT EXISTS quest_types (
    type_id integer NOT NULL,
    type_key character varying(100) NOT NULL,
    type_name character varying(255) NOT NULL,
    difficulty_level character varying(50) DEFAULT 'medium'::character varying NOT NULL
);

-- 🔹 Условия начала квеста
CREATE TABLE IF NOT EXISTS quest_conditions (
    condition_id integer NOT NULL,
    condition_key character varying(100) NOT NULL,
    condition_name character varying(255) NOT NULL
);

-- 🔹 Требования к выполнению
CREATE TABLE IF NOT EXISTS quest_requirements (
    requirement_id integer NOT NULL,
    requirement_key character varying(100) NOT NULL,
    requirement_name character varying(255) NOT NULL,
    requirement_value character varying(255) NOT NULL
);

-- 🔹 Награды за выполнение
CREATE TABLE IF NOT EXISTS quest_rewards (
    id integer NOT NULL,
    reward_key character varying(100) NOT NULL,
    reward_name text NOT NULL,
    reward_value integer NOT NULL,
    reward_type text NOT NULL,
    reward_description text
);
