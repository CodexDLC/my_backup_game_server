--
-- PostgreSQL database dump
--

-- Dumped from database version 17.4
-- Dumped by pg_dump version 17.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: reputation; Type: TABLE; Schema: public; Owner: codexen
--

CREATE TABLE public.reputation (
    reputation_id integer NOT NULL,
    character_id integer,
    faction_id integer,
    reputation_value integer DEFAULT 0 NOT NULL,
    reputation_status character varying(50) DEFAULT 'neutral'::character varying NOT NULL
);


ALTER TABLE public.reputation OWNER TO codexen;

--
-- Name: reputation_reputation_id_seq; Type: SEQUENCE; Schema: public; Owner: codexen
--

CREATE SEQUENCE public.reputation_reputation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reputation_reputation_id_seq OWNER TO codexen;

--
-- Name: reputation_reputation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codexen
--

ALTER SEQUENCE public.reputation_reputation_id_seq OWNED BY public.reputation.reputation_id;


--
-- Name: special_stat_effects; Type: TABLE; Schema: public; Owner: codexen
--

CREATE TABLE public.special_stat_effects (
    stat_key character varying(50) NOT NULL,
    effect_field character varying(50) NOT NULL,
    multiplier numeric(12,4) NOT NULL,
    description text
);


ALTER TABLE public.special_stat_effects OWNER TO codexen;

--
-- Name: state_entities; Type: TABLE; Schema: public; Owner: codexen
--

CREATE TABLE public.state_entities (
    id integer NOT NULL,
    access_code integer NOT NULL,
    code_name text NOT NULL,
    ui_type text NOT NULL,
    description text DEFAULT ''::text,
    is_active boolean DEFAULT true
);


ALTER TABLE public.state_entities OWNER TO codexen;

--
-- Name: state_entities_discord; Type: TABLE; Schema: public; Owner: codexen
--

CREATE TABLE public.state_entities_discord (
    guild_id bigint NOT NULL,
    world_id uuid NOT NULL,
    access_code integer NOT NULL,
    role_name text NOT NULL,
    role_id bigint NOT NULL,
    permissions integer DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.state_entities_discord OWNER TO codexen;

--
-- Name: state_entities_id_seq; Type: SEQUENCE; Schema: public; Owner: codexen
--

CREATE SEQUENCE public.state_entities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.state_entities_id_seq OWNER TO codexen;

--
-- Name: state_entities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: codexen
--

ALTER SEQUENCE public.state_entities_id_seq OWNED BY public.state_entities.id;


--
-- Name: reputation reputation_id; Type: DEFAULT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.reputation ALTER COLUMN reputation_id SET DEFAULT nextval('public.reputation_reputation_id_seq'::regclass);


--
-- Name: state_entities id; Type: DEFAULT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities ALTER COLUMN id SET DEFAULT nextval('public.state_entities_id_seq'::regclass);


--
-- Data for Name: reputation; Type: TABLE DATA; Schema: public; Owner: codexen
--

COPY public.reputation (reputation_id, character_id, faction_id, reputation_value, reputation_status) FROM stdin;
\.


--
-- Data for Name: special_stat_effects; Type: TABLE DATA; Schema: public; Owner: codexen
--

COPY public.special_stat_effects (stat_key, effect_field, multiplier, description) FROM stdin;
\.


--
-- Data for Name: state_entities; Type: TABLE DATA; Schema: public; Owner: codexen
--

COPY public.state_entities (id, access_code, code_name, ui_type, description, is_active) FROM stdin;
1	1	Странник	status_flag		t
2	2	Игрок_оф	status_flag	Offline player	t
3	3	Игрок_он	status_flag	Online player	t
4	4	Администратор	system_flag	Administrator role	t
5	5	Модератор	system_flag	Moderator role	t
6	6	Тестер	system_flag	Tester role	t
\.


--
-- Data for Name: state_entities_discord; Type: TABLE DATA; Schema: public; Owner: codexen
--

COPY public.state_entities_discord (guild_id, world_id, access_code, role_name, role_id, permissions, created_at, updated_at) FROM stdin;
\.


--
-- Name: reputation_reputation_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codexen
--

SELECT pg_catalog.setval('public.reputation_reputation_id_seq', 1, false);


--
-- Name: state_entities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: codexen
--

SELECT pg_catalog.setval('public.state_entities_id_seq', 6, true);


--
-- Name: reputation reputation_pkey; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.reputation
    ADD CONSTRAINT reputation_pkey PRIMARY KEY (reputation_id);


--
-- Name: special_stat_effects special_stat_effects_pkey; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.special_stat_effects
    ADD CONSTRAINT special_stat_effects_pkey PRIMARY KEY (stat_key, effect_field);


--
-- Name: state_entities state_entities_access_code_key; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities
    ADD CONSTRAINT state_entities_access_code_key UNIQUE (access_code);


--
-- Name: state_entities state_entities_code_name_key; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities
    ADD CONSTRAINT state_entities_code_name_key UNIQUE (code_name);


--
-- Name: state_entities_discord state_entities_discord_pkey; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities_discord
    ADD CONSTRAINT state_entities_discord_pkey PRIMARY KEY (guild_id, access_code);


--
-- Name: state_entities state_entities_pkey; Type: CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities
    ADD CONSTRAINT state_entities_pkey PRIMARY KEY (id);


--
-- Name: idx_state_entities_access_code; Type: INDEX; Schema: public; Owner: codexen
--

CREATE INDEX idx_state_entities_access_code ON public.state_entities USING btree (access_code);


--
-- Name: idx_state_entities_code_name; Type: INDEX; Schema: public; Owner: codexen
--

CREATE INDEX idx_state_entities_code_name ON public.state_entities USING btree (code_name);


--
-- Name: idx_state_entities_discord_role_id; Type: INDEX; Schema: public; Owner: codexen
--

CREATE INDEX idx_state_entities_discord_role_id ON public.state_entities_discord USING btree (role_id);


--
-- Name: idx_state_entities_discord_updated_at; Type: INDEX; Schema: public; Owner: codexen
--

CREATE INDEX idx_state_entities_discord_updated_at ON public.state_entities_discord USING btree (updated_at);


--
-- Name: idx_state_entities_ui_type; Type: INDEX; Schema: public; Owner: codexen
--

CREATE INDEX idx_state_entities_ui_type ON public.state_entities USING btree (ui_type);


--
-- Name: reputation reputation_character_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.reputation
    ADD CONSTRAINT reputation_character_id_fkey FOREIGN KEY (character_id) REFERENCES public.characters(character_id) ON DELETE CASCADE;


--
-- Name: state_entities_discord state_entities_discord_world_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: codexen
--

ALTER TABLE ONLY public.state_entities_discord
    ADD CONSTRAINT state_entities_discord_world_id_fkey FOREIGN KEY (world_id) REFERENCES public.worlds(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

