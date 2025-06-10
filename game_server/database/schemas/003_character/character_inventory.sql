-- 🔹 Экипированные предметы
CREATE TABLE IF NOT EXISTS equipped_items (
    character_id INTEGER PRIMARY KEY,  -- ✅ Теперь `character_id` — уникальный идентификатор
    inventory_id INTEGER NOT NULL,
    slot CHARACTER VARYING(50),
    durability INTEGER DEFAULT 100 NOT NULL,
    enchantment_effect JSON
);

-- 🔹 Инвентарь персонажа
CREATE TABLE IF NOT EXISTS inventory (
    inventory_id SERIAL PRIMARY KEY,  -- ✅ `inventory_id` остаётся основным идентификатором
    character_id INTEGER NOT NULL,
    item_id INTEGER,
    quantity INTEGER DEFAULT 1 NOT NULL,
    acquired_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
