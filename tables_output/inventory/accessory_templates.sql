CREATE TABLE IF NOT EXISTS accessory_templates (
    id integer NOT NULL,
    base_item_code integer NOT NULL,
    suffix_code integer NOT NULL,
    name text NOT NULL,
    rarity integer NOT NULL,
    color text NOT NULL,
    energy_pool_bonus integer,
    regen_energy_rate double precision,
    magic_defense_bonus integer,
    absorption_bonus double precision,
    reflect_damage double precision,
    damage_boost double precision,
    durability integer DEFAULT 0 NOT NULL,
    excluded_bonus_type text,
    effect_description text,
    is_fragile boolean DEFAULT false NOT NULL,
    strength_percentage double precision DEFAULT 0 NOT NULL
)
