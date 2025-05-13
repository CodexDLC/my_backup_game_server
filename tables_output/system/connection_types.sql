CREATE TABLE public.connection_types (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying NOT NULL,
    description text,
    time_cost integer NOT NULL
)
