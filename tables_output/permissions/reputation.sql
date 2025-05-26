CREATE TABLE IF NOT EXISTS reputation (
    reputation_id integer NOT NULL,
    character_id integer,
    faction_id integer,
    reputation_value integer DEFAULT 0 NOT NULL,
    reputation_status character varying(50) DEFAULT 'neutral'::character varying NOT NULL
)
