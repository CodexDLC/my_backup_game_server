-- Таблица: equipment_templates
-- Хранит шаблоны для всех экипируемых предметов (оружие, броня, одежда, аксессуары).
-- Эти шаблоны будут генерироваться и храниться в ограниченном пуле.
CREATE TABLE IF NOT EXISTS equipment_templates (
    template_id SERIAL PRIMARY KEY, -- Уникальный идентификатор шаблона
    item_code VARCHAR(255) NOT NULL UNIQUE, -- Уникальный код для конкретного сгенерированного шаблона (например, LEGENDARY_LONGSWORD_OF_VAMPIRISM_RIFT_MITHRIL_T7)
    
    -- Общие метаданные предмета
    display_name VARCHAR(255) NOT NULL, -- Отображаемое имя предмета (например, "Legendary Broadsword of Vampirism")
    category VARCHAR(50) NOT NULL,     -- Категория предмета (WEAPON, ARMOR, APPAREL, ACCESSORY)
    sub_category VARCHAR(50) NOT NULL, -- Субкатегория (ONE_HANDED_SWORD, HEAVY_CHEST, APPAREL_TORSO_COMMON, RING_BASIC)
    equip_slot VARCHAR(50) NOT NULL,   -- Слот экипировки (MAIN_HAND, HEAD, TORSO_ARMOR, RING)
    inventory_size VARCHAR(10) NOT NULL, -- Размер в инвентаре (например, "2x3")
    
    -- Ссылки на компоненты, из которых был сгенерирован шаблон
    material_code VARCHAR(255) NOT NULL, -- material_code материала, из которого сделан предмет (для разложения)
    suffix_code VARCHAR(255),            -- Ссылка на суффикс (опционально, может быть NULL если нет суффикса)
    
    -- Модификаторы и характеристики шаблона (ПРЕДРАССЧИТАННЫЕ)
    -- Эти значения уже включают влияние rarity_level материала и value_tiers модификаторов
    base_modifiers_json JSONB NOT NULL DEFAULT '{}', -- JSONB поле для всех численных модификаторов (урон, защита, HP_steal и т.д.)
                                                      -- Пример: {"physical_attack": 15.5, "fire_resistance": 0.08, "energy_pool_bonus": 25}
    
    -- Специфические поля для одежды
    quality_tier VARCHAR(50), -- Качество/статус одежды (NEW, WORN, RICH) - NULL для других категорий
    
    -- Метаданные для генератора
    rarity_level INTEGER NOT NULL, -- Уровень редкости материала, который был использован (от 1 до 8, или 9 для "без редкости")
    
    -- Другие общие поля (если нужны)
    icon_url VARCHAR(255),         -- Иконка предмета (NULLABLE)
    description TEXT,              -- Описание предмета (NULLABLE)
    
    -- Ограничения и индексы
    CONSTRAINT fk_material_code FOREIGN KEY (material_code) REFERENCES materials(material_code) ON DELETE RESTRICT
    -- CONSTRAINT fk_suffix_code FOREIGN KEY (suffix_code) REFERENCES suffixes(suffix_code) ON DELETE SET NULL -- Если будет отдельная таблица для суффиксов
);

-- Индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_equipment_category ON equipment_templates (category);
CREATE INDEX IF NOT EXISTS idx_equipment_subcategory ON equipment_templates (sub_category);
CREATE INDEX IF NOT EXISTS idx_equipment_equip_slot ON equipment_templates (equip_slot);
CREATE INDEX IF NOT EXISTS idx_equipment_rarity_level ON equipment_templates (rarity_level);




-- Таблица: instanced_items
-- Хранит уникальные экземпляры предметов, выданных игрокам или монстрам.
-- Эти предметы материализуются из шаблонов equipment_templates или static_item_templates.
CREATE TABLE IF NOT EXISTS instanced_items (
    instance_id SERIAL PRIMARY KEY,    -- Уникальный идентификатор экземпляра предмета
    
    template_id INTEGER NOT NULL,      -- Ссылка на шаблон предмета (из equipment_templates или static_item_templates)
    is_equippable BOOLEAN NOT NULL,    -- Флаг: true если это экипируемый предмет, false если статический
    
    -- Информация о владельце и местоположении
    owner_id INTEGER NOT NULL,         -- ID владельца (character_id, monster_id, container_id, vendor_id, auction_id)
    owner_type VARCHAR(20) NOT NULL,   -- Тип владельца ('CHARACTER', 'MONSTER', 'CONTAINER', 'VENDOR', 'AUCTION_HOUSE')
    location_type VARCHAR(50) NOT NULL, -- Местоположение предмета (INVENTORY, EQUIPPED, STORAGE, VENDOR_STOCK, AUCTION_LISTING, CORPSE_LOOT)
    location_slot VARCHAR(50),         -- Слот экипировки (HEAD, MAIN_HAND, RING_1, etc.) или номер слота в инвентаре/хранилище - NULLABLE (если, например, в контейнере без специфичного слота)

    -- Финальные, рандомизированные характеристики предмета
    -- Эти значения уже включают все скаляции, roll-ы и рандомизацию.
    final_modifiers_json JSONB NOT NULL DEFAULT '{}', -- JSONB поле для всех финальных численных модификаторов предмета
    
    -- Дублирование некоторых ключевых свойств шаблона для быстрого доступа
    display_name VARCHAR(255) NOT NULL,
    item_category VARCHAR(50) NOT NULL, -- Категория предмета (WEAPON, ARMOR, APPAREL, ACCESSORY, CONSUMABLE, etc.)
    item_sub_category VARCHAR(50),      -- Субкатегория предмета (NULLABLE, если не применимо)
    inventory_size VARCHAR(10),         -- Размер в инвентаре (например, "2x3") - NULLABLE, если предмет, например, это золото без размера

    -- Состояние экземпляра
    current_durability INTEGER,         -- Если будет введена механика "прочности" для экземпляров. NULL, если нет.
    current_stack_size INTEGER NOT NULL DEFAULT 1, -- Текущий размер стака (для стакаемых предметов)
    
    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_instance_owner_location ON instanced_items (owner_id, owner_type, location_type);
    CREATE INDEX IF NOT EXISTS idx_instance_template_id ON instanced_items (template_id);
    CREATE INDEX IF NOT EXISTS idx_instance_item_category ON instanced_items (item_category);
);


-- Таблица: materials
-- Хранит информацию о всех материалах (базовых и разломных), используемых для генерации предметов.
CREATE TABLE IF NOT EXISTS materials (
    material_code VARCHAR(255) PRIMARY KEY, -- Уникальный код материала (например, "COPPER", "RIFT_MITHRIL", "DRAGON_HIDE")
    name VARCHAR(255) NOT NULL,            -- Читаемое имя материала (например, "Copper", "Rift Mithril")
    type VARCHAR(50) NOT NULL,             -- Тип материала (METAL, FABRIC, LEATHER)
    material_category VARCHAR(20) NOT NULL, -- Категория материала (BASE, RIFT)
    rarity_level INTEGER,                  -- Уровень редкости для RIFT материалов (1-8), NULL для BASE материалов (или 9 для no-rarity)
    adjective VARCHAR(255) NOT NULL,       -- Прилагательное, используемое для формирования имени предмета (например, "Copper", "Rift Mithril")
    color VARCHAR(7) NOT NULL,             -- Цвет материала (HEX-код, например, "#FFD700")
    is_fragile BOOLEAN NOT NULL,           -- Флаг хрупкости (true/false)
    strength_percentage DOUBLE PRECISION NOT NULL, -- Процент усиления модификаторов предмета, созданного из этого материала
    
    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_materials_type ON materials (type);
    CREATE INDEX IF NOT EXISTS idx_materials_category ON materials (material_category);
    CREATE INDEX IF NOT EXISTS idx_materials_rarity_level ON materials (rarity_level);
);


-- Таблица: suffixes
-- Хранит информацию о суффиксах, которые могут быть применены к предметам.
-- ВЕРСИЯ 2.0 (с группами)
CREATE TABLE IF NOT EXISTS suffixes (
    suffix_code VARCHAR(255) PRIMARY KEY, -- Уникальный код суффикса
    "group" VARCHAR(100) NOT NULL,        -- (НОВОЕ ПОЛЕ) Логическая группа суффикса (например, "VAMPIRIC", "ARCANE")
    fragment VARCHAR(255) NOT NULL,       -- Текстовый фрагмент для имени предмета
    modifiers JSONB NOT NULL DEFAULT '[]' -- Модификаторы, которые дает суффикс
);

-- Индекс для быстрого поиска по группе
CREATE INDEX IF NOT EXISTS ix_suffixes_group ON suffixes ("group");



-- Таблица: modifier_library
-- Хранит централизованную библиотеку всех возможных модификаторов,
-- используемых для предметов и характеристик персонажей/монстров.
CREATE TABLE IF NOT EXISTS modifier_library (
    modifier_code VARCHAR(255) PRIMARY KEY, -- Уникальный код модификатора (например, "HP_STEAL_PERCENT", "FIRE_RESISTANCE")
    name VARCHAR(255) NOT NULL,            -- Читаемое имя модификатора (например, "Health Steal")
    effect_description TEXT NOT NULL,      -- Описание эффекта модификатора
    value_tiers JSONB NOT NULL,            -- JSONB поле для словаря value_tiers (например, {"1": 0.01, "2": 0.02, ...})
    randomization_range DOUBLE PRECISION NOT NULL, -- Диапазон случайного разброса (например, 0.3 для +/- 30%)
    
    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_modifier_name ON modifier_library (name);
);


-- Таблица: static_item_templates
-- Хранит шаблоны для всех неэкипируемых предметов (мусор, квестовые, расходные, ремесленные материалы и т.д.).
CREATE TABLE IF NOT EXISTS static_item_templates (
    template_id SERIAL PRIMARY KEY, -- Уникальный идентификатор шаблона
    item_code VARCHAR(255) NOT NULL UNIQUE, -- Уникальный код для статического предмета (например, POTION_HEALTH_MINOR, QUEST_ITEM_LOST_MAP)
    
    display_name VARCHAR(255) NOT NULL, -- Отображаемое имя предмета
    category VARCHAR(50) NOT NULL,     -- Категория предмета (CONSUMABLE, QUEST, CRAFTING_MATERIAL, JUNK, CURRENCY, LORE)
    sub_category VARCHAR(50),          -- Подкатегория (например, "Potion", "Map", "Ore") - NULLABLE
    
    inventory_size VARCHAR(10) NOT NULL, -- Размер в инвентаре (например, "1x1", "1x2")
    stackable BOOLEAN NOT NULL DEFAULT FALSE, -- Можно ли стакать предмет
    max_stack_size INTEGER DEFAULT 1,     -- Максимальное количество в одном стаке (1 для не-стакаемых)
    
    base_value INTEGER NOT NULL DEFAULT 0, -- Базовая стоимость предмета (для продажи торговцам)
    
    icon_url VARCHAR(255),         -- Иконка предмета (NULLABLE)
    description TEXT,              -- Описание предмета (NULLABLE)
    
    -- Дополнительные свойства, специфичные для статических предметов (могут быть в JSONB или отдельных полях)
    properties_json JSONB NOT NULL DEFAULT '{}' -- JSONB поле для других специфических свойств (например, "heal_amount", "quest_id", "lore_text")
);

-- Индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_static_item_category ON static_item_templates (category);
CREATE INDEX IF NOT EXISTS idx_static_item_subcategory ON static_item_templates (sub_category);




-- Таблица: item_base
-- Хранит "метаданные 0 уровня" - базовые архетипы предметов.
-- Эти данные являются входными для генератора, не ссылаются на другие таблицы,
-- но используются для создания записей в equipment_templates.
CREATE TABLE IF NOT EXISTS item_base (
    base_item_code VARCHAR(255) PRIMARY KEY, -- Уникальный код архетипа (например, "DAGGER", "LIGHT_CHEST", "RING_BASIC")
                                             -- Это будет sub_category_code из YAML-файлов Archetype_Names.yml
    
    category VARCHAR(50) NOT NULL,          -- Категория предмета (WEAPON, ARMOR, APPAREL, ACCESSORY)
    
    -- Динамические свойства архетипа, включая имена-синонимы и базовые характеристики
    -- Пример: {"names": ["Dagger", "Knife"], "damage_type": "Piercing", "base_roll_dice": "1d4", "inventory_size": "1x1", "equip_slot": "MAIN_HAND"}
    properties_json JSONB NOT NULL DEFAULT '{}'
);

-- Индексы для оптимизации поиска
CREATE INDEX IF NOT EXISTS idx_item_base_category ON item_base (category);