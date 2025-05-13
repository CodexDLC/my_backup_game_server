CREATE TABLE public.quest_flags (
    flag_id integer NOT NULL,
    flag_key character varying(100) NOT NULL,
    quest_key integer,
    step_key character varying(100),
    flag_key_template character varying(100),
    value text NOT NULL
)
