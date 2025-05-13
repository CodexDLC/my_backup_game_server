-- Файл: core_items.sql
-- Полная структура генерации предметов, их модификаций и шаблонов

-- 🔹 Шаблоны аксессуаров
CREATE TABLE public.accessory_templates (
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
);

-- 🔹 Шаблоны брони
CREATE TABLE public.armor_templates (
    id integer NOT NULL,
    base_item_code integer NOT NULL,
    suffix_code integer NOT NULL,
    name text NOT NULL,
    rarity integer NOT NULL,
    color text NOT NULL,
    physical_defense integer NOT NULL,
    magical_defense integer,
    durability integer NOT NULL,
    weight integer NOT NULL,
    energy_regeneration_bonus double precision,
    anti_crit double precision,
    dodge_chance double precision,
    hp_percent double precision,
    armor_boost integer,
    armor_percent_boost double precision,
    counter_attack double precision,
    anti_dodge double precision,
    effect_description text,
    allowed_for_class text,
    visual_asset text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_fragile boolean DEFAULT false NOT NULL,
    strength_percentage double precision DEFAULT 0 NOT NULL
);

-- 🔹 Базовые материалы
CREATE TABLE public.materials (
    id integer NOT NULL,
    name text,
    prefix text,
    color text,
    is_fragile boolean,
    strength_percentage integer
);

-- 🔹 Библиотека модификаторов
CREATE TABLE public.modifiers_library (
    id integer NOT NULL,
    access_modifier integer NOT NULL,
    modifier_name text NOT NULL,
    effect_description text
);

-- 🔹 Суффиксы предметов
CREATE TABLE public.suffixes (
    suffix_code integer NOT NULL,
    fragment text NOT NULL,
    is_for_weapon boolean NOT NULL,
    is_for_armor boolean NOT NULL,
    is_for_accessory boolean NOT NULL,
    mod1_code integer,
    mod1_value numeric,
    mod2_code integer,
    mod2_value numeric,
    mod3_code integer,
    mod3_value numeric,
    mod4_code integer,
    mod4_value numeric
);

-- 🔹 Стандартные модификаторы
CREATE TABLE public.template_modifier_defaults (
    base_item_code integer NOT NULL,
    access_modifier integer NOT NULL,
    default_value numeric NOT NULL
);

-- 🔹 Шаблоны оружия
CREATE TABLE public.weapon_templates (
    id integer NOT NULL,
    base_item_code integer NOT NULL,
    suffix_code integer NOT NULL,
    name text NOT NULL,
    rarity integer NOT NULL,
    color text NOT NULL,
    p_atk integer,
    m_atk integer,
    crit_chance double precision,
    crit_damage_bonus double precision,
    armor_penetration double precision,
    durability integer,
    accuracy double precision,
    hp_steal_percent double precision DEFAULT 0,
    effect_description text,
    allowed_for_class text,
    visual_asset text,
    is_fragile boolean DEFAULT false NOT NULL,
    strength_percentage double precision DEFAULT 0 NOT NULL
);

-- 🔹 Базовые предметы
CREATE TABLE public.item_base (
    base_item_code integer NOT NULL,
    item_name text NOT NULL,
    category text NOT NULL,
    equip_slot text NOT NULL,
    base_durability integer NOT NULL,
    base_weight integer NOT NULL
);
