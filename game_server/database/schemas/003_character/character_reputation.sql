-- Файл: character_reputation.sql
-- Заглушка для механики репутации персонажа

CREATE TABLE IF NOT EXISTS reputation (
    reputation_id integer NOT NULL,
    character_id integer,
    faction_id integer,
    reputation_value integer DEFAULT 0 NOT NULL,
    reputation_status character varying(50) DEFAULT 'neutral'::character varying NOT NULL
);

-- 🔹 Будущие расширения:
-- 1️⃣ Добавить систему влияния фракций
-- 2️⃣ Динамическое изменение репутации по событиям
-- 3️⃣ Логи взаимодействий персонажа с фракциями

-- Пока заглушка, но готова к дальнейшему развитию!
