CREATE TABLE IF NOT EXISTS abilities (
    ability_key character varying(100) NOT NULL,
    ability_type character varying(50) NOT NULL,
    params jsonb NOT NULL,
    description text
)
