CREATE TABLE public.skill_unlocks (
    skill_key character varying(100) NOT NULL,
    rank smallint NOT NULL,
    xp_threshold bigint NOT NULL,
    rank_name character varying(100) NOT NULL
)
