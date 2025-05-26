CREATE TABLE IF NOT EXISTS skill_ability_unlocks (
    skill_key character varying(100) NOT NULL,
    level smallint NOT NULL,
    ability_key character varying(100) NOT NULL
)
