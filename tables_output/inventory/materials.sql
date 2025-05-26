CREATE TABLE IF NOT EXISTS materials (
    id integer NOT NULL,
    name text,
    prefix text,
    color text,
    is_fragile boolean,
    strength_percentage integer
)
