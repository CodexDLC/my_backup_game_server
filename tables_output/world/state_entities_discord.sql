CREATE TABLE IF NOT EXISTS state_entities_discord (
    guild_id bigint NOT NULL,
    world_id uuid NOT NULL,
    access_code integer NOT NULL,
    role_name text NOT NULL,
    role_id bigint NOT NULL,
    permissions integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
)
