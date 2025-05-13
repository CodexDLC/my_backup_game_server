CREATE TABLE public.discord_bindings (
    guild_id bigint NOT NULL,
    world_id uuid NOT NULL,
    entity_access_key character varying NOT NULL,
    category_id character varying,
    channel_id character varying,
    permissions integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
)
