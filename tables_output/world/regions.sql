CREATE TABLE IF NOT EXISTS regions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    world_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text
)
