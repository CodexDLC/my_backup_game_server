-- Файл: character_combat.sql
-- Боевые характеристики персонажа

CREATE TABLE IF NOT EXISTS player_magic_attack (
    player_id integer NOT NULL,
    elemental_power_bonus double precision,
    fire_power_bonus double precision,
    water_power_bonus double precision,
    air_power_bonus double precision,
    earth_power_bonus double precision,
    light_power_bonus double precision,
    dark_power_bonus double precision,
    gray_magic_power_bonus double precision
);

CREATE TABLE IF NOT EXISTS player_magic_defense (
    player_id integer NOT NULL,
    fire_resistance double precision,
    water_resistance double precision,
    air_resistance double precision,
    earth_resistance double precision,
    light_resistance double precision,
    dark_resistance double precision,
    gray_magic_resistance double precision,
    magic_resistance_percent double precision
);

CREATE TABLE IF NOT EXISTS player_physical_attack (
    player_id integer NOT NULL,
    piercing_damage_bonus double precision,
    slashing_damage_bonus double precision,
    blunt_damage_bonus double precision,
    cutting_damage_bonus double precision
);

CREATE TABLE IF NOT EXISTS player_physical_defense (
    player_id integer NOT NULL,
    piercing_resistance double precision,
    slashing_resistance double precision,
    blunt_resistance double precision,
    cutting_resistance double precision,
    physical_resistance_percent double precision
);

CREATE TABLE IF NOT EXISTS character_status (
    player_id integer NOT NULL,  -- Идентификатор персонажа, который ссылается на character_id
    current_health integer,
    max_health integer,
    current_energy integer,
    crit_chance double precision,
    crit_damage_bonus double precision,
    anti_crit_chance double precision,
    anti_crit_damage double precision,
    dodge_chance double precision,
    anti_dodge_chance double precision,
    counter_attack_chance double precision,
    parry_chance double precision,
    block_chance double precision,
    armor_penetration double precision,
    physical_attack double precision,
    magical_attack double precision,
    magic_resistance double precision,
    physical_resistance double precision,
    mana_cost_reduction double precision,
    regen_health_rate double precision,
    energy_regeneration_bonus double precision,
    energy_pool_bonus integer,
    absorption_bonus double precision,
    shield_value double precision,
    shield_regeneration double precision,
    CONSTRAINT fk_character FOREIGN KEY (player_id) REFERENCES characters(character_id) ON DELETE CASCADE  -- Внешний ключ для связи с characters
);
