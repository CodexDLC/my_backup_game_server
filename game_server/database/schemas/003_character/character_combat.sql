-- 🔹 Боевые характеристики персонажа: магическая атака
CREATE TABLE IF NOT EXISTS player_magic_attack (
    character_id INTEGER PRIMARY KEY,  -- ✅ Исправлено: `character_id`
    elemental_power_bonus DOUBLE PRECISION,
    fire_power_bonus DOUBLE PRECISION,
    water_power_bonus DOUBLE PRECISION,
    air_power_bonus DOUBLE PRECISION,
    earth_power_bonus DOUBLE PRECISION,
    light_power_bonus DOUBLE PRECISION,
    dark_power_bonus DOUBLE PRECISION,
    gray_magic_power_bonus DOUBLE PRECISION
);

-- 🔹 Магическая защита персонажа
CREATE TABLE IF NOT EXISTS player_magic_defense (
    character_id INTEGER PRIMARY KEY,  -- ✅ Исправлено: `character_id`
    fire_resistance DOUBLE PRECISION,
    water_resistance DOUBLE PRECISION,
    air_resistance DOUBLE PRECISION,
    earth_resistance DOUBLE PRECISION,
    light_resistance DOUBLE PRECISION,
    dark_resistance DOUBLE PRECISION,
    gray_magic_resistance DOUBLE PRECISION,
    magic_resistance_percent DOUBLE PRECISION
);

-- 🔹 Физическая атака персонажа
CREATE TABLE IF NOT EXISTS player_physical_attack (
    character_id INTEGER PRIMARY KEY,  -- ✅ Исправлено: `character_id`
    piercing_damage_bonus DOUBLE PRECISION,
    slashing_damage_bonus DOUBLE PRECISION,
    blunt_damage_bonus DOUBLE PRECISION,
    cutting_damage_bonus DOUBLE PRECISION
);

-- 🔹 Физическая защита персонажа
CREATE TABLE IF NOT EXISTS player_physical_defense (
    character_id INTEGER PRIMARY KEY,  -- ✅ Исправлено: `character_id`
    piercing_resistance DOUBLE PRECISION,
    slashing_resistance DOUBLE PRECISION,
    blunt_resistance DOUBLE PRECISION,
    cutting_resistance DOUBLE PRECISION,
    physical_resistance_percent DOUBLE PRECISION
);

-- 🔹 Статус персонажа
CREATE TABLE IF NOT EXISTS character_status (
    character_id INTEGER PRIMARY KEY,  -- ✅ Уникальный ключ
    current_health INTEGER DEFAULT 0,
    max_health INTEGER DEFAULT 0,
    current_energy INTEGER DEFAULT 0,
    crit_chance DOUBLE PRECISION DEFAULT 0,
    crit_damage_bonus DOUBLE PRECISION DEFAULT 0,
    anti_crit_chance DOUBLE PRECISION DEFAULT 0,
    anti_crit_damage DOUBLE PRECISION DEFAULT 0,
    dodge_chance DOUBLE PRECISION DEFAULT 0,
    anti_dodge_chance DOUBLE PRECISION DEFAULT 0,
    counter_attack_chance DOUBLE PRECISION DEFAULT 0,
    parry_chance DOUBLE PRECISION DEFAULT 0,
    block_chance DOUBLE PRECISION DEFAULT 0,
    armor_penetration DOUBLE PRECISION DEFAULT 0,
    physical_attack DOUBLE PRECISION DEFAULT 0,
    magical_attack DOUBLE PRECISION DEFAULT 0,
    magic_resistance DOUBLE PRECISION DEFAULT 0,
    physical_resistance DOUBLE PRECISION DEFAULT 0,
    mana_cost_reduction DOUBLE PRECISION DEFAULT 0,
    regen_health_rate DOUBLE PRECISION DEFAULT 0,
    energy_regeneration_bonus DOUBLE PRECISION DEFAULT 0,
    energy_pool_bonus INTEGER DEFAULT 0,
    absorption_bonus DOUBLE PRECISION DEFAULT 0,
    shield_value DOUBLE PRECISION DEFAULT 0,
    shield_regeneration DOUBLE PRECISION DEFAULT 0,
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(character_id) ON DELETE CASCADE
);
