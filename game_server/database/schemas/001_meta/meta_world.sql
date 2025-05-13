CREATE TABLE public.connection_types (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying NOT NULL,
    description text,
    time_cost integer NOT NULL
)


-- Файл: meta_world.sql
-- Основные параметры миров, регионов и свойств сущностей

CREATE TABLE public.worlds (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying NOT NULL,
    is_static boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE public.regions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    world_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text
);

CREATE TABLE public.subregions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    region_id uuid NOT NULL,
    access_key character varying NOT NULL,
    name character varying NOT NULL,
    description text,
    is_peaceful boolean DEFAULT false NOT NULL
);

CREATE TABLE public.entity_properties (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type character varying NOT NULL,
    entity_id uuid NOT NULL,
    key character varying NOT NULL,
    value text
);

CREATE TABLE public.entity_state_map (
    entity_access_key character varying NOT NULL,
    access_code integer NOT NULL
);

CREATE TABLE public.connections (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    from_type character varying NOT NULL,
    from_id uuid NOT NULL,
    to_type character varying NOT NULL,
    to_id uuid NOT NULL,
    type_id uuid NOT NULL,
    one_click boolean DEFAULT false NOT NULL,
    difficulty integer DEFAULT 1 NOT NULL,
    CONSTRAINT connections_from_type_check CHECK (((from_type)::text = ANY ((ARRAY['region'::character varying, 'subregion'::character varying])::text[]))),
    CONSTRAINT connections_to_type_check CHECK (((to_type)::text = ANY ((ARRAY['region'::character varying, 'subregion'::character varying])::text[])))
)

CREATE TABLE public.connection_types (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying NOT NULL,
    description text,
    time_cost integer NOT NULL
);


CREATE TABLE public.state_entities (
    id integer NOT NULL,
    access_code integer NOT NULL,
    code_name text NOT NULL,
    ui_type text NOT NULL,
    description text DEFAULT ''::text,
    is_active boolean DEFAULT true
);