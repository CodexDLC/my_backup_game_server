CREATE TABLE IF NOT EXISTS quests (
    quest_id integer NOT NULL,
    quest_key integer NOT NULL,
    quest_name character varying(255) NOT NULL,
    description_key character varying(100) NOT NULL,
    reward_key character varying(100) NOT NULL,
    progress_flag character varying(255) DEFAULT NULL::character varying,
    status character varying(50) DEFAULT 'inactive'::character varying NOT NULL
)
