CREATE TABLE IF NOT EXISTS skills (
    skill_id integer NOT NULL,
    skill_key character varying(100) NOT NULL,
    name character varying(255),
    skill_group character varying(50),
    main_special character varying(50),
    secondary_special character varying(50)
)
