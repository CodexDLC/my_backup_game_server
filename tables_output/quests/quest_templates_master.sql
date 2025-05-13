CREATE TABLE public.quest_templates_master (
    template_id integer NOT NULL,
    template_key character varying(100) NOT NULL,
    type_key character varying(100),
    condition_key character varying(100),
    requirement_key character varying(100),
    reward_key character varying(100)
)
