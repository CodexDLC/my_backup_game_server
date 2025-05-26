CREATE TABLE IF NOT EXISTS quest_rewards (
    id integer NOT NULL,
    reward_key character varying(100) NOT NULL,
    reward_name text NOT NULL,
    reward_value integer NOT NULL,
    reward_type text NOT NULL,
    reward_description text
)
