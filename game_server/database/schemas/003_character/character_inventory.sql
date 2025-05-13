CREATE TABLE public.equipped_items (
    character_id integer NOT NULL,
    inventory_id integer NOT NULL,
    slot character varying(50),
    durability integer DEFAULT 100 NOT NULL,
    enchantment_effect json
)

CREATE TABLE public.inventory (
    inventory_id integer NOT NULL,
    character_id integer NOT NULL,
    item_id integer,
    quantity integer DEFAULT 1 NOT NULL,
    acquired_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
)
