CREATE TABLE public.quest_types (
    type_id integer NOT NULL,
    type_key character varying(100) NOT NULL,
    type_name character varying(255) NOT NULL,
    difficulty_level character varying(50) DEFAULT 'medium'::character varying NOT NULL
)
