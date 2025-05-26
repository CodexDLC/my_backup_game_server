CREATE TABLE IF NOT EXISTS quest_requirements (
    requirement_id integer NOT NULL,
    requirement_key character varying(100) NOT NULL,
    requirement_name character varying(255) NOT NULL,
    requirement_value character varying(255) NOT NULL
)
