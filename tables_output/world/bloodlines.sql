CREATE TABLE IF NOT EXISTS bloodlines (
    bloodline_id integer NOT NULL,
    bloodline_name character varying(100) DEFAULT 'human'::character varying NOT NULL
)
