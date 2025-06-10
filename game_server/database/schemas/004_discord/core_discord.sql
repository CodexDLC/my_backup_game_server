-- 🔹 Привязка мира к Discord-серверу
CREATE TABLE IF NOT EXISTS discord_bindings (
    guild_id BIGINT NOT NULL,
    world_id UUID NOT NULL,
    entity_access_key CHARACTER VARYING NOT NULL,
    category_id CHARACTER VARYING,
    channel_id CHARACTER VARYING,
    permissions INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (guild_id, world_id) -- ✅ Композитный ключ
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
    guild_id BIGINT NOT NULL,
    world_id UUID NOT NULL,
    access_code INTEGER NOT NULL,
    role_name TEXT NOT NULL,
    role_id BIGINT NOT NULL,
    permissions INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
    PRIMARY KEY (guild_id, world_id, access_code) -- ✅ Композитный ключ
);

-- 🔹 Описания квестов для Discord
CREATE TABLE IF NOT EXISTS discord_quest_descriptions (
    description_key CHARACTER VARYING(100) PRIMARY KEY, -- ✅ Уникальный ключ
    text TEXT NOT NULL
);
