-- 🔹 Типы соединений
CREATE TABLE IF NOT EXISTS connection_types (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,  -- ✅ Уникальный идентификатор
    name character varying NOT NULL,
    description text,
    time_cost integer NOT NULL
);

-- 🔹 Основные параметры миров
CREATE TABLE IF NOT EXISTS worlds (
    world_id uuid DEFAULT gen_random_uuid() PRIMARY KEY, -- ✅ ИЗМЕНЕНО: world_id теперь PRIMARY KEY (соответствует модели)
    name character varying NOT NULL, -- Колонка 'name' в DDL соответствует 'world_name' в модели
    is_static boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


-- 🔹 Основные параметры регионов
CREATE TABLE IF NOT EXISTS regions (
    id uuid DEFAULT gen_random_uuid() NOT NULL, -- Не PK, но уникальный ID
    access_key character varying NOT NULL PRIMARY KEY, -- Теперь это PK
    world_id uuid NOT NULL,
    name character varying NOT NULL, -- Соответствует region_name в модели
    description text
);

-- 🔹 Основные параметры субрегионов
CREATE TABLE IF NOT EXISTS subregions (
    id uuid NOT NULL DEFAULT gen_random_uuid(), -- ✅ ИЗМЕНЕНО: id теперь обычная колонка, не PK
    region_id uuid NOT NULL, -- ✅ ИЗМЕНЕНО: колонка region_id для FK на regions.id
    access_key character varying NOT NULL PRIMARY KEY, -- ✅ ИЗМЕНЕНО: access_key теперь PRIMARY KEY (соответствует модели)
    name character varying NOT NULL,
    description text,
    is_peaceful boolean DEFAULT false NOT NULL
    -- parent_access_key отсутствует в DDL, так как теперь FK через region_id
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
    access_code character varying(50) PRIMARY KEY,
    code_name text NOT NULL,
    ui_type text NOT NULL,
    description text DEFAULT ''::text,
    is_active boolean DEFAULT true,
    created_at timestamp with time zone NOT NULL DEFAULT now()
);
