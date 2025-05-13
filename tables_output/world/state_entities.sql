CREATE TABLE public.state_entities (
    id integer NOT NULL,
    access_code integer NOT NULL,
    code_name text NOT NULL,
    ui_type text NOT NULL,
    description text DEFAULT ''::text,
    is_active boolean DEFAULT true
)
