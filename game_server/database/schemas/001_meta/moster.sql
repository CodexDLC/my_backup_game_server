CREATE TABLE IF NOT EXISTS elite_monsters (
    monster_instance_id SERIAL PRIMARY KEY, -- Уникальный ID экземпляра элитного монстра (не путать с template_id монстра)
    monster_template_id INTEGER NOT NULL,  -- Ссылка на базовый шаблон монстра (если есть такая таблица, например, 'monster_templates')
    
    display_name VARCHAR(255) NOT NULL,    -- Отображаемое имя элитного монстра (может включать префикс "Elite" или имя игрока)
    current_location VARCHAR(255) NOT NULL, -- Текущая локация, где монстр находится
    last_player_killed_id INTEGER,          -- ID последнего игрока, которого убил этот монстр (NULLABLE, если монстр не убивал игроков)
    killed_players_count INTEGER NOT NULL DEFAULT 0, -- Счетчик убитых игроков этим монстром
    
    current_status VARCHAR(50) NOT NULL DEFAULT 'IDLE_IN_POOL', -- Текущий статус монстра: ACTIVE_IN_WORLD, DEAD, RESPAWNING, IDLE_IN_POOL
    killed_by_info_json JSONB NOT NULL DEFAULT '{}', -- Информация о том, кто убил монстра (одиночка, группа, клан, рейд)
                                                     -- Пример: {"type": "character", "id": 123, "name": "HeroName"}
                                                     -- Пример: {"type": "group", "ids": [123, 456], "names": ["Hero1", "Hero2"], "group_name": "Awesome Group"}
                                                     -- Пример: {"type": "clan", "id": 789, "name": "Valiant Clan"}
    
    -- Если у монстра есть уникальные статы или модификаторы, помимо экипировки
    unique_modifiers_json JSONB NOT NULL DEFAULT '{}', -- JSONB для уникальных модификаторов этого элитного монстра
    
    -- Дополнительные флаги или метаданные
    is_active BOOLEAN NOT NULL DEFAULT TRUE, -- Флаг активности (для быстрого фильтра, дублирует current_status)
    spawn_priority INTEGER NOT NULL DEFAULT 1, -- Приоритет появления в подземельях
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE,
    
    -- Индексы
    CREATE INDEX IF NOT EXISTS idx_elite_monster_location ON elite_monsters (current_location);
    CREATE INDEX IF NOT EXISTS idx_elite_monster_player_killed ON elite_monsters (last_player_killed_id);
    CREATE INDEX IF NOT EXISTS idx_elite_monster_active ON elite_monsters (is_active);
    CREATE INDEX IF NOT EXISTS idx_elite_monster_status ON elite_monsters (current_status);

    -- Возможно, добавится FK на character_id, если будет таблица characters
    -- CONSTRAINT fk_last_player_killed FOREIGN KEY (last_player_killed_id) REFERENCES characters(character_id) ON DELETE SET NULL
);