CREATE TABLE public.subregions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    region_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    is_peaceful boolean DEFAULT false NOT NULL
)
