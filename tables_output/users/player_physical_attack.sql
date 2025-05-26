CREATE TABLE IF NOT EXISTS player_physical_attack (
    player_id integer NOT NULL,
    piercing_damage_bonus double precision,
    slashing_damage_bonus double precision,
    blunt_damage_bonus double precision,
    cutting_damage_bonus double precision
)
