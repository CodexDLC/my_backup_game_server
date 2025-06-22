-- Таблица: combat_parameters_reference
-- Эта таблица является справочником (шпаргалкой) для разработчика.
-- Она описывает все возможные боевые и производные характеристики персонажей,
-- которые могут быть использованы в игровой логике, расчетах и MongoDB-слепках.
-- Эта таблица НЕ ПРЕДНАЗНАЧЕНА для создания в реальной базе данных.
-- Все ее данные будут вычисляться или храниться в динамическом слепке персонажа в MongoDB.

CREATE TABLE IF NOT EXISTS combat_parameters_reference (
    -- Уникальный строковый ключ для идентификации параметра
    parameter_key VARCHAR(100) PRIMARY KEY,

    -- Отображаемое имя параметра (для удобства чтения и документации)
    display_name VARCHAR(255) NOT NULL,

    -- Подробное описание параметра и его назначения в игре
    description TEXT,

    -- Категория, к которой относится параметр (например, "Магическая атака", "Физическая защита", "Состояние")
    category VARCHAR(50) NOT NULL,

    -- Ожидаемый тип данных этого параметра (для валидации и типизации в коде)
    data_type VARCHAR(50) NOT NULL, -- (e.g., 'INTEGER', 'DOUBLE PRECISION', 'BOOLEAN')

    -- Единицы измерения параметра, если применимо (например, 'HP', '%', 'урон')
    unit VARCHAR(20),

    -- Флаг, указывающий, является ли параметр производным (вычисляемым) от других характеристик
    -- True: вычисляется из статов, экипировки, баффов (например, crit_chance, total_physical_attack)
    -- False: является базовым состоянием (current_health, current_energy)
    is_derived BOOLEAN DEFAULT TRUE NOT NULL,

    -- Флаг, указывающий, отображается ли этот параметр игроку в UI
    is_player_displayable BOOLEAN DEFAULT TRUE NOT NULL,

    -- Флаг, указывающий, является ли эффект параметра отрицательным (для стилизации UI)
    is_negative_effect BOOLEAN DEFAULT FALSE NOT NULL
);

-- Пример вставки данных (необязательно, но полезно для шпаргалки)
INSERT INTO combat_parameters_reference (parameter_key, display_name, description, category, data_type, unit, is_derived, is_player_displayable, is_negative_effect) VALUES
('current_health', 'Текущее здоровье', 'Текущее количество очков здоровья персонажа.', 'Состояние', 'INTEGER', 'HP', FALSE, TRUE, FALSE),
('max_health', 'Максимальное здоровье', 'Максимально возможное количество очков здоровья персонажа.', 'Состояние', 'INTEGER', 'HP', TRUE, TRUE, FALSE),
('current_energy', 'Текущая энергия', 'Текущее количество очков энергии (маны/выносливости) персонажа.', 'Состояние', 'INTEGER', 'Энергия', FALSE, TRUE, FALSE),
('crit_chance', 'Шанс критического удара', 'Вероятность нанесения критического урона в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('crit_damage_bonus', 'Бонус критического урона', 'Дополнительный урон при критическом ударе в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('anti_crit_chance', 'Шанс анти-крита', 'Вероятность избежать критического урона противника в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('anti_crit_damage', 'Анти-крит урон', 'Снижение критического урона от противника в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('dodge_chance', 'Шанс уклонения', 'Вероятность полностью избежать входящего урона в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('anti_dodge_chance', 'Шанс анти-уклонения', 'Снижение шанса уклонения противника в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('counter_attack_chance', 'Шанс контратаки', 'Вероятность нанести ответный удар после уклонения/блока.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('parry_chance', 'Шанс парирования', 'Вероятность полностью отразить/парировать входящий физический урон.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('block_chance', 'Шанс блокирования', 'Вероятность уменьшить входящий урон с помощью блока.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('armor_penetration', 'Пробивание брони', 'Уменьшение эффективности брони противника в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('physical_attack', 'Физическая атака', 'Общая сила физических атак персонажа.', 'Боевые параметры', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('magical_attack', 'Магическая атака', 'Общая сила магических атак персонажа.', 'Боевые параметры', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('magic_resistance', 'Магическое сопротивление', 'Снижение входящего магического урона в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('physical_resistance', 'Физическое сопротивление', 'Снижение входящего физического урона в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('mana_cost_reduction', 'Снижение затрат маны', 'Уменьшение стоимости магических способностей в процентах.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('regen_health_rate', 'Скорость регенерации здоровья', 'Количество здоровья, восстанавливаемое за единицу времени.', 'Боевые параметры', 'DOUBLE PRECISION', 'HP/сек', TRUE, TRUE, FALSE),
('energy_regeneration_bonus', 'Бонус регенерации энергии', 'Увеличение скорости восстановления энергии.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('energy_pool_bonus', 'Бонус к запасу энергии', 'Дополнительное максимальное количество энергии.', 'Боевые параметры', 'INTEGER', 'Энергия', TRUE, TRUE, FALSE),
('absorption_bonus', 'Бонус поглощения', 'Процент поглощения входящего урона.', 'Боевые параметры', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('shield_value', 'Значение щита', 'Количество урона, которое может поглотить щит.', 'Боевые параметры', 'DOUBLE PRECISION', 'щит', TRUE, TRUE, FALSE),
('shield_regeneration', 'Регенерация щита', 'Скорость восстановления щита за единицу времени.', 'Боевые параметры', 'DOUBLE PRECISION', 'щит/сек', TRUE, TRUE, FALSE),
('elemental_power_bonus', 'Бонус стихийной силы', 'Общий бонус к силе всех стихийных атак.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('fire_power_bonus', 'Бонус силы огня', 'Дополнительный урон огнем.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('water_power_bonus', 'Бонус силы воды', 'Дополнительный урон водой.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('air_power_bonus', 'Бонус силы воздуха', 'Дополнительный урон воздухом.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('earth_power_bonus', 'Бонус силы земли', 'Дополнительный урон землей.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('light_power_bonus', 'Бонус силы света', 'Дополнительный урон светом.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('dark_power_bonus', 'Бонус силы тьмы', 'Дополнительный урон тьмой.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('gray_magic_power_bonus', 'Бонус силы серой магии', 'Дополнительный урон серой магией.', 'Магическая атака', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('fire_resistance', 'Сопротивление огню', 'Снижение урона огнем.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('water_resistance', 'Сопротивление воде', 'Снижение урона водой.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('air_resistance', 'Сопротивление воздуху', 'Снижение урона воздухом.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('earth_resistance', 'Сопротивление земле', 'Снижение урона землей.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('light_resistance', 'Сопротивление свету', 'Снижение урона светом.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('dark_resistance', 'Сопротивление тьме', 'Снижение урона тьмой.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('gray_magic_resistance', 'Сопротивление серой магии', 'Снижение урона серой магией.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('magic_resistance_percent', 'Общее магическое сопротивление', 'Общее снижение всего магического урона.', 'Магическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('piercing_damage_bonus', 'Бонус пробивающего урона', 'Дополнительный пробивающий урон.', 'Физическая атака', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('slashing_damage_bonus', 'Бонус рубящего урона', 'Дополнительный рубящий урон.', 'Физическая атака', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('blunt_damage_bonus', 'Бонус дробящего урона', 'Дополнительный дробящий урон.', 'Физическая атака', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('cutting_damage_bonus', 'Бонус режущего урона', 'Дополнительный режущий урон.', 'Физическая атака', 'DOUBLE PRECISION', 'урон', TRUE, TRUE, FALSE),
('piercing_resistance', 'Сопротивление пробивающему урону', 'Снижение пробивающего урона.', 'Физическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('slashing_resistance', 'Сопротивление рубящему урону', 'Снижение рубящего урона.', 'Физическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('blunt_resistance', 'Сопротивление дробящему урону', 'Снижение дробящего урона.', 'Физическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('cutting_resistance', 'Сопротивление режущему урону', 'Снижение режущего урона.', 'Физическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE),
('physical_resistance_percent', 'Общее физическое сопротивление', 'Общее снижение всего физического урона.', 'Физическая защита', 'DOUBLE PRECISION', '%', TRUE, TRUE, FALSE);

