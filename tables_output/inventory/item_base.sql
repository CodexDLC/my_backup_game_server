CREATE TABLE IF NOT EXISTS item_base (
    base_item_code integer NOT NULL,
    item_name text NOT NULL,
    category text NOT NULL,
    equip_slot text NOT NULL,
    base_durability integer NOT NULL,
    base_weight integer NOT NULL
)
