-- 🔹 Типы соединений
CREATE TABLE IF NOT EXISTS connection_types (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    name character varying NOT NULL,
    description text,
    time_cost integer NOT NULL
);

-- 🔹 Основные параметры миров
CREATE TABLE IF NOT EXISTS worlds (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    name character varying NOT NULL,
    is_static boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

-- 🔹 Основные параметры регионов
CREATE TABLE IF NOT EXISTS regions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    world_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text
);

-- 🔹 Основные параметры субрегионов
CREATE TABLE IF NOT EXISTS subregions (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    region_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    is_peaceful boolean DEFAULT false NOT NULL
);

-- 🔹 Свойства сущностей
CREATE TABLE IF NOT EXISTS entity_properties (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    entity_type character varying NOT NULL,
    entity_id uuid NOT NULL,
    key character varying NOT NULL,
    value text
);

-- 🔹 Карта состояний сущностей
CREATE TABLE IF NOT EXISTS entity_state_map (
    entity_access_key character varying NOT NULL,
    access_code integer NOT NULL,
    PRIMARY KEY (entity_access_key, access_code)  -- ✅ Композитный ключ
);

-- 🔹 Сущности состояний
CREATE TABLE IF NOT EXISTS state_entities (
    id SERIAL PRIMARY KEY,  -- ✅ Уникальный идентификатор
    access_code integer NOT NULL,
    code_name text NOT NULL,
    ui_type text NOT NULL,
    description text DEFAULT ''::text,
    is_active boolean DEFAULT true
);
