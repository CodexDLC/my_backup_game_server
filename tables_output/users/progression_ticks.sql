CREATE TABLE IF NOT EXISTS progression_ticks (
    tick_id integer NOT NULL,
    character_id integer,
    skill_id integer,
    xp_generated integer,
    "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
)
