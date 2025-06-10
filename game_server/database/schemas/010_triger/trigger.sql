-- 🔹 Удаляем существующие функции перед созданием новых



-- 🔹 Функция для добавления навыков персонажа
CREATE FUNCTION insert_character_skills()
RETURNS TRIGGER AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM character_skills WHERE character_id = NEW.character_id) THEN
        INSERT INTO character_skills (character_id, skill_key, level, xp, progress_state)
        SELECT NEW.character_id, skill_key, 0, 0, 'PAUSE' FROM skills;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER after_character_insert
AFTER INSERT ON characters
FOR EACH ROW
EXECUTE FUNCTION insert_character_skills();

-- 🔹 Функция для добавления характеристик персонажа
CREATE FUNCTION insert_character_special()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO characters_special (character_id, strength, perception, endurance, agility, intelligence, charisma, luck)
    VALUES (NEW.character_id, 5, 5, 5, 5, 5, 5, 5);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_character_insert_special
AFTER INSERT ON characters
FOR EACH ROW
EXECUTE FUNCTION insert_character_special();

-- 🔹 Функция для добавления статуса персонажа
CREATE FUNCTION insert_character_status()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO character_status (character_id, current_health, max_health, current_energy)
    VALUES (NEW.character_id, 0, 0, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_character_insert_status
AFTER INSERT ON characters
FOR EACH ROW
EXECUTE FUNCTION insert_character_status();

-- 🔹 Функция для добавления XP данных персонажа
CREATE FUNCTION insert_xp_tick_data()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO xp_tick_data (character_id, skill_id, xp_generated)
    SELECT NEW.character_id, skill_key, 0 
    FROM skills
    WHERE skill_key NOT IN (SELECT skill_key FROM character_skills WHERE character_id = NEW.character_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- 🔹 Функция для ограничения одного online-персонажа на аккаунт
CREATE FUNCTION enforce_single_online_character()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM characters WHERE account_id = NEW.account_id AND status = 'online') >= 1 THEN
        RAISE EXCEPTION 'Только один персонаж может быть online на аккаунт %', NEW.account_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;




-- 🔹 Функция для проверки лимита персонажей (замена CHECK)
CREATE FUNCTION check_max_characters()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM characters WHERE account_id = NEW.account_id HAVING COUNT(*) >= 5) THEN
        RAISE EXCEPTION 'Максимум 5 персонажей на аккаунт!';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
