CREATE TABLE IF NOT EXISTS suffixes (
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
)
