-- 🔹 Привязка мира к Discord-серверу
CREATE TABLE IF NOT EXISTS discord_bindings (
    guild_id BIGINT NOT NULL,
    world_id UUID NOT NULL, -- Теперь это обычная колонка, не часть PK
    entity_access_key CHARACTER VARYING NOT NULL, -- Эта колонка становится частью PK
    category_id CHARACTER VARYING,
    channel_id CHARACTER VARYING,
    permissions INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (guild_id, entity_access_key) -- Измененный первичный ключ
);

-- 🔹 Назначенные разрешения Discord-ролям
CREATE TABLE IF NOT EXISTS applied_permissions (
    guild_id BIGINT NOT NULL,
    entity_access_key CHARACTER VARYING NOT NULL,
    access_code INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (guild_id, entity_access_key, access_code) -- ✅ Композитный ключ
);

-- 🔹 Управление ролями и доступами в Discord
CREATE TABLE IF NOT EXISTS state_entities_discord (
    guild_id bigint NOT NULL,       -- ID Discord-сервера (часть PK)
    role_id bigint NOT NULL,        -- Discord ID роли (часть PK)
    
    access_code character varying(50) NULL, -- <--- ИЗМЕНЕНО: Может быть NULL, не часть PK. FK к state_entities.access_code
    role_name text NOT NULL,        -- Имя роли в Discord
    permissions character varying(50) NULL, -- Опциональный строковый флаг разрешений (например, 'read_only', 'admin_only')
    
    created_at timestamp with time zone NOT NULL DEFAULT now(),
    updated_at timestamp with time zone NOT NULL DEFAULT now(),

    PRIMARY KEY (guild_id, role_id) -- <--- ИЗМЕНЕНО: Композитный PK теперь guild_id и role_id
);