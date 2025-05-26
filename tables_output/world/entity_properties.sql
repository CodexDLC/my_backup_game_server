CREATE TABLE IF NOT EXISTS entity_properties (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type character varying NOT NULL,
    entity_id uuid NOT NULL,
    key character varying NOT NULL,
    value text
)
