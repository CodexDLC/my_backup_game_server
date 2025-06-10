-- Файл: character_reputation.sql
-- Заглушка для механики репутации персонажа

-- 🔹 Таблица репутации персонажа
CREATE TABLE IF NOT EXISTS reputation (
    character_id INTEGER PRIMARY KEY,  -- ✅ `character_id` теперь уникальный ключ
    faction_id INTEGER,
    reputation_value INTEGER DEFAULT 0 NOT NULL,
    reputation_status CHARACTER VARYING(50) DEFAULT 'neutral'::character varying NOT NULL
);


-- 🔹 Будущие расширения:
-- 1️⃣ Добавить систему влияния фракций
-- 2️⃣ Динамическое изменение репутации по событиям
-- 3️⃣ Логи взаимодействий персонажа с фракциями

-- Пока заглушка, но готова к дальнейшему развитию!
