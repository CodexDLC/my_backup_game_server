CREATE TABLE IF NOT EXISTS discord_bindings (
    guild_id bigint NOT NULL,
    world_id uuid NOT NULL,
    entity_access_key character varying NOT NULL,
    category_id character varying,
    channel_id character varying,
    permissions integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE IF NOT EXISTS applied_permissions (
    guild_id bigint NOT NULL,
    entity_access_key character varying NOT NULL,
    access_code integer NOT NULL,
    target_type text NOT NULL,
    target_id bigint NOT NULL,
    role_id bigint NOT NULL,
    applied_at timestamp with time zone DEFAULT now() NOT NULL
);

-- Файл: core_discord.sql
-- Управление ролями и доступами в Discord

CREATE TABLE IF NOT EXISTS state_entities_discord (
    guild_id bigint NOT NULL,
    world_id uuid NOT NULL,
    access_code integer NOT NULL,
    role_name text NOT NULL,
    role_id bigint NOT NULL,
    permissions integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


CREATE TABLE IF NOT EXISTS discord_quest_descriptions (
    description_key character varying(100) NOT NULL,
    text text NOT NULL
);