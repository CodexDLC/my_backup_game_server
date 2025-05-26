CREATE TABLE IF NOT EXISTS quest_steps (
    step_key character varying(100) NOT NULL,
    quest_key integer NOT NULL,
    step_order integer NOT NULL,
    description_key character varying(100) NOT NULL,
    visibility_condition character varying(255),
    reward_key character varying(100),
    status character varying(50) NOT NULL
)
