CREATE TABLE public.special_stat_effects (
    stat_key character varying(50) NOT NULL,
    effect_field character varying(50) NOT NULL,
    multiplier numeric(12,4) NOT NULL,
    description text
)
