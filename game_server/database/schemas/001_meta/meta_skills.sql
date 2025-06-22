
CREATE TABLE IF NOT EXISTS special_stat_effects (
    effect_id SERIAL PRIMARY KEY,               -- Уникальный ID для каждого конкретного правила влияния.
    
    stat_key VARCHAR(50) NOT NULL,             -- ✅ ХАРАКТЕРИСТИКА-ИСТОЧНИК: Например, 'Strength', 'Agility', 'Intelligence'.
                                                -- Это базовая характеристика, которая оказывает влияние.

    affected_property VARCHAR(100) NOT NULL,    -- ✅ СВОЙСТВО-ЦЕЛЬ: Например, 'MaxHealth', 'MeleeDamage', 'CritChance', 'SpellPower', 'MoveSpeed'.
                                                -- Игровой параметр, на который влияет характеристика.

    effect_type VARCHAR(50) NOT NULL,           -- ✅ ТИП ВЛИЯНИЯ:
                                                -- 'flat_bonus_per_point': Добавляет фиксированное значение за каждую единицу stat_key. (Пример: +2 HP за 1 Endurance)
                                                -- 'percentage_bonus_per_point': Добавляет процентный бонус за каждую единицу stat_key. (Пример: +0.5% к урону за 1 Strength)
                                                -- 'set_base_value': Устанавливает базовое значение для affected_property, если stat_key достигает определённого порога (менее часто).
                                                -- (Можно добавить 'threshold_bonus', 'scaling_factor' и т.д. по мере необходимости.)

    value NUMERIC(12,4) NOT NULL,               -- ✅ ЗНАЧЕНИЕ ЭФФЕКТА: Числовое значение, используемое в зависимости от effect_type.
                                                -- Если 'flat_bonus_per_point', то 10 (для 10 HP).
                                                -- Если 'percentage_bonus_per_point', то 0.005 (для 0.5%).
    
    calculation_order INTEGER DEFAULT 100,      -- Порядок применения эффектов, если несколько влияют на одно и то же свойство.
                                                -- Важно для сложных расчётов: сначала одни эффекты, потом другие.
    description TEXT,                           -- Описание этого правила влияния.
    
    -- Ограничение, чтобы для каждой характеристики и свойства был только один уникальный тип влияния
    CONSTRAINT uq_stat_property_effect_type UNIQUE (stat_key, affected_property, effect_type)
);


CREATE TABLE IF NOT EXISTS abilities (
    ability_id SERIAL PRIMARY KEY,              -- Уникальный ID способности
    ability_key VARCHAR(100) NOT NULL UNIQUE,   -- Уникальный строковый ключ способности (например, 'FIREBALL', 'SHIELD_BASH', 'CRITICAL_STRIKE_MASTERY')
    name VARCHAR(255) NOT NULL,                 -- Отображаемое имя способности
    description TEXT,                           -- Полное описание эффекта способности
    ability_type VARCHAR(50) NOT NULL,          -- Тип способности: 'active', 'passive', 'toggle' (переключаемая)
    
    -- Требования для изучения/разблокировки способности
    required_skill_key VARCHAR(50),             -- Ссылка на skill_key, необходимый для этой способности (например, 'FIRE_MAGIC')
    required_skill_level INTEGER DEFAULT 0,     -- Минимальный уровень в required_skill_key для разблокировки
    required_stats JSONB,                       -- JSONB: Требования к характеристикам (например, {"Intelligence": 15})
    required_items JSONB,                       -- JSONB: Требуемые предметы/экипировка для использования (например, {"weapon_type": "staff"})

    -- Эффекты и затраты способности
    cost_type VARCHAR(50),                      -- Тип затрат: 'mana', 'stamina', 'energy', 'none'
    cost_amount INTEGER DEFAULT 0,              -- Количество затрат
    cooldown_seconds INTEGER DEFAULT 0,         -- Время перезарядки в секундах
    cast_time_ms INTEGER DEFAULT 0,             -- Время применения в миллисекундах
    effect_data JSONB,                          -- JSONB: Детальные параметры эффекта способности (например, {"damage_type": "fire", "base_damage": 10, "scaling_stat": "Intelligence"})
    
    -- Визуальные/аудио эффекты
    animation_key VARCHAR(100),                 -- Ключ анимации, связанной со способностью
    sfx_key VARCHAR(100),                       -- Ключ звукового эффекта
    vfx_key VARCHAR(100),                       -- Ключ визуального эффекта

    CONSTRAINT fk_ability_skill_key FOREIGN KEY (required_skill_key) REFERENCES skills(skill_key) ON DELETE SET NULL
);



CREATE TABLE IF NOT EXISTS skill_exclusions (
    exclusion_id SERIAL PRIMARY KEY,            -- Уникальный ID для каждой группы исключений
    group_name VARCHAR(100) NOT NULL UNIQUE,   -- Название группы исключений (например, 'Light_Dark_Magic', 'Elemental_Affinity'). Используется для логической группировки.
    description TEXT,                           -- Подробное описание этой группы исключений и её назначения.
    exclusion_type VARCHAR(50) NOT NULL,        -- Тип правила исключения:
                                                -- 'mutually_exclusive': Только один навык из этой группы может быть активен ('PLUS').
                                                -- 'debuff_on_others': Активация одного навыка дебаффает (меняет статус) другие в группе, но не обязательно исключает их полностью.
    
    excluded_skills JSONB NOT NULL,             -- JSONB-массив строковых `skill_key` (из таблицы `skills`), которые входят в эту группу.
                                                -- Пример: '["LIGHT_MAGIC", "DARK_MAGIC"]'
                                                -- Пример: '["FIRE_MAGIC", "WATER_MAGIC", "EARTH_MAGIC", "AIR_MAGIC"]'
    
    exclusion_effect JSONB                      -- JSONB-объект, описывающий эффект, который применяется к исключенным навыкам.
                                                -- Пример для 'mutually_exclusive': '{"on_exclude_set_state": "PAUSE"}'
                                                -- Пример для 'debuff_on_others': '{"on_exclude_set_state": "MINUS", "level_penalty_percent": 10}'
);


CREATE TABLE IF NOT EXISTS skills (
    skill_key VARCHAR(50) PRIMARY KEY,
    skill_id INTEGER UNIQUE, -- Убрали автоинкремент из DDL, т.к. он управляется ORM

    -- --- Поля, приведенные в соответствие с моделью ---
    name VARCHAR(100) NOT NULL,
    description TEXT,
    stat_influence JSON NOT NULL, -- Тип изменен на JSON и добавлен NOT NULL
    is_magic BOOLEAN NOT NULL DEFAULT FALSE,
    rarity_weight INTEGER NOT NULL DEFAULT 100,
    category_tag VARCHAR(50) NOT NULL,
    role_preference_tag VARCHAR(100),
    limit_group_tag VARCHAR(100),
    max_level INTEGER NOT NULL DEFAULT 1, -- DEFAULT изменен на 1

    -- --- Удаленные поля, которых нет в модели ---
    -- skill_group VARCHAR(50),
    -- main_special VARCHAR(50),
    -- secondary_special VARCHAR(50)
);