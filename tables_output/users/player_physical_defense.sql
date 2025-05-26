CREATE TABLE IF NOT EXISTS player_physical_defense (
    player_id integer NOT NULL,
    piercing_resistance double precision,
    slashing_resistance double precision,
    blunt_resistance double precision,
    cutting_resistance double precision,
    physical_resistance_percent double precision
)
