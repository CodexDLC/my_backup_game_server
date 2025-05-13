-- Файл: meta_skills.sql
-- Полная структура системы навыков, их прокачки и эффектов

-- 🔹 Основной список навыков
CREATE TABLE public.skills (
    skill_id integer NOT NULL,
    skill_key character varying(100) NOT NULL,
    name character varying(255),
    skill_group character varying(50),
    main_special character varying(50),
    secondary_special character varying(50)
);

-- 🔹 Эффекты, связанные с навыками
CREATE TABLE public.special_stat_effects (
    stat_key character varying(50) NOT NULL,
    effect_field character varying(50) NOT NULL,
    multiplier numeric(12,4) NOT NULL,
    description text
);

-- 🔹 Разблокировка умений через навыки
CREATE TABLE public.skill_ability_unlocks (
    skill_key character varying(100) NOT NULL,
    level smallint NOT NULL,
    ability_key character varying(100) NOT NULL
);

-- 🔹 Разблокировка уровней навыков
CREATE TABLE public.skill_unlocks (
    skill_key character varying(100) NOT NULL,
    rank smallint NOT NULL,
    xp_threshold bigint NOT NULL,
    rank_name character varying(100) NOT NULL
);

CREATE TABLE public.abilities (
    ability_key character varying(100) NOT NULL,
    ability_type character varying(50) NOT NULL,
    params jsonb NOT NULL,
    description text
);

-- Table: special_stat_effects
CREATE TABLE public.special_stat_effects (
    stat_key character varying(50) NOT NULL,
    effect_field character varying(50) NOT NULL,
    multiplier numeric(12,4) NOT NULL,
    description text
);