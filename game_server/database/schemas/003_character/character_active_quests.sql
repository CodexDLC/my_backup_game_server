CREATE TABLE IF NOT EXISTS active_quests (
    character_id integer NOT NULL,
    quest_id integer NOT NULL,
    quest_key character varying(100),
    status character varying(50) DEFAULT 'active'::character varying NOT NULL,
    current_step integer DEFAULT 1 NOT NULL,
    flags_status json,
    completion_time timestamp without time zone,
    failure_reason character varying(255)
);

