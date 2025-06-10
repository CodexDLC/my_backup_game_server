CREATE TABLE IF NOT EXISTS skill_unlocks (
    skill_key VARCHAR(50) NOT NULL, -- Строковый ключ навыка, соответствует skills.skill_key
    level SMALLINT NOT NULL,        -- ✅ ИЗМЕНЕНО: Уровень навыка (например, 1, 2, 3, 4, 5)
    xp_threshold BIGINT NOT NULL,   -- Общее количество XP, необходимое для достижения этого уровня
    level_name VARCHAR(100) NOT NULL,-- ✅ ИЗМЕНЕНО: Название этого уровня (например, "Новичок", "Подмастерье")

    PRIMARY KEY (skill_key, level), -- Композитный PRIMARY KEY теперь включает skill_key и level

    CONSTRAINT fk_skill_key FOREIGN KEY (skill_key) REFERENCES skills(skill_key) ON DELETE CASCADE
);
