CREATE TABLE IF NOT EXISTS character_skills (
    character_id integer NOT NULL,
    skill_id integer NOT NULL,
    level integer DEFAULT 1 NOT NULL,
    xp bigint DEFAULT 0 NOT NULL,
    progress_state character varying(10) DEFAULT 'PLUS'::character varying NOT NULL,
    CONSTRAINT character_skills_progress_state_check CHECK (((progress_state)::text = ANY ((ARRAY['PLUS'::character varying, 'PAUSE'::character varying, 'MINUS'::character varying])::text[])))
)
