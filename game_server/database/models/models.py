from typing import List, Optional
from sqlalchemy import TIMESTAMP, BigInteger, Boolean, CheckConstraint, Column, DateTime, Double, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, PrimaryKeyConstraint, SmallInteger, String, Table, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from datetime import datetime, timezone
import decimal
import uuid


class Base(DeclarativeBase):
    pass


class Abilities(Base):
    __tablename__ = 'abilities'
    __table_args__ = (
        PrimaryKeyConstraint('ability_key', name='abilities_pkey'),
    )

    ability_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    ability_type: Mapped[str] = mapped_column(String(50))
    params: Mapped[dict] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(Text)

    skill_ability_unlocks: Mapped[List['SkillAbilityUnlocks']] = relationship('SkillAbilityUnlocks', back_populates='abilities')


class AccessoryTemplates(Base):
    __tablename__ = 'accessory_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='accessory_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer)
    suffix_code: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    rarity: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(Text)
    durability: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'))
    energy_pool_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    regen_energy_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    magic_defense_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    reflect_damage: Mapped[Optional[float]] = mapped_column(Double(53))
    damage_boost: Mapped[Optional[float]] = mapped_column(Double(53))
    excluded_bonus_type: Mapped[Optional[str]] = mapped_column(Text)
    effect_description: Mapped[Optional[str]] = mapped_column(Text)


class AccountInfo(Base):
    __tablename__ = 'account_info'
    __table_args__ = (
        PrimaryKeyConstraint('account_id', name='account_info_pkey'),
        UniqueConstraint('discord_id', name='account_info_discord_id_key'),
        UniqueConstraint('email', name='account_info_email_key'),
        UniqueConstraint('game_id', name='account_info_game_id_key'),
        UniqueConstraint('google_id', name='account_info_google_id_key'),
        UniqueConstraint('steam_id', name='account_info_steam_id_key'),
        UniqueConstraint('telegram_id', name='account_info_telegram_id_key'),
        UniqueConstraint('twitch_id', name='account_info_twitch_id_key'),
        UniqueConstraint('twitter_id', name='account_info_twitter_id_key'),
        UniqueConstraint('username', name='account_info_username_key')
    )

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, server_default=text("nextval('account_info_account_id_seq')"))
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'website'"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'active'"))
    role: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'user'"))
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    google_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    discord_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    telegram_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    twitter_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    steam_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    twitch_id: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    game_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)
    linked_platforms: Mapped[Optional[str]] = mapped_column(Text)
    auth_token: Mapped[Optional[str]] = mapped_column(Text)
    avatar: Mapped[Optional[str]] = mapped_column(Text)
    locale: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))


class ActiveQuests(Base):
    __tablename__ = 'active_quests'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', 'quest_id', name='active_quests_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(50), server_default=text("'active'::character varying"))
    current_step: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    quest_key: Mapped[Optional[str]] = mapped_column(String(100))
    flags_status: Mapped[Optional[dict]] = mapped_column(JSON)
    completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255))


class AppliedSqlFiles(Base):
    __tablename__ = 'applied_sql_files'
    __table_args__ = (
        PrimaryKeyConstraint('filename', name='applied_sql_files_pkey'),
    )

    filename: Mapped[str] = mapped_column(Text, primary_key=True)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('now()'))


class ArmorTemplates(Base):
    __tablename__ = 'armor_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='armor_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer)
    suffix_code: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    rarity: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(Text)
    physical_defense: Mapped[int] = mapped_column(Integer)
    durability: Mapped[int] = mapped_column(Integer)
    weight: Mapped[int] = mapped_column(Integer)
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'))
    magical_defense: Mapped[Optional[int]] = mapped_column(Integer)
    energy_regeneration_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_crit: Mapped[Optional[float]] = mapped_column(Double(53))
    dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    hp_percent: Mapped[Optional[float]] = mapped_column(Double(53))
    armor_boost: Mapped[Optional[int]] = mapped_column(Integer)
    armor_percent_boost: Mapped[Optional[float]] = mapped_column(Double(53))
    counter_attack: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_dodge: Mapped[Optional[float]] = mapped_column(Double(53))
    effect_description: Mapped[Optional[str]] = mapped_column(Text)
    allowed_for_class: Mapped[Optional[str]] = mapped_column(Text)
    visual_asset: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'))
    





class Bloodlines(Base):
    __tablename__ = 'bloodlines'
    __table_args__ = (
        PrimaryKeyConstraint('bloodline_id', name='bloodlines_pkey'),
    )

    bloodline_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bloodline_name: Mapped[str] = mapped_column(String(100), server_default=text("'human'::character varying"))


class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='characters_pkey'),
        UniqueConstraint('account_id', name='unique_account')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    race_id: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    surname: Mapped[Optional[str]] = mapped_column(String(100))
    bloodline_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    tick_events: Mapped[List['TickEvents']] = relationship('TickEvents', back_populates='character')
    tick_summary: Mapped[List['TickSummary']] = relationship('TickSummary', back_populates='character')


class CharactersSpecial(Base):
    __tablename__ = 'characters_special'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='characters_special_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strength: Mapped[Optional[int]] = mapped_column(Integer)
    perception: Mapped[Optional[int]] = mapped_column(Integer)
    endurance: Mapped[Optional[int]] = mapped_column(Integer)
    agility: Mapped[Optional[int]] = mapped_column(Integer)
    intelligence: Mapped[Optional[int]] = mapped_column(Integer)
    charisma: Mapped[Optional[int]] = mapped_column(Integer)
    luck: Mapped[Optional[int]] = mapped_column(Integer)


class ConnectionTypes(Base):
    __tablename__ = 'connection_types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='connection_types_pkey'),
        UniqueConstraint('name', name='connection_types_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String)
    time_cost: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)

    connections: Mapped[List['Connections']] = relationship('Connections', back_populates='type')


class DiscordQuestDescriptions(Base):
    __tablename__ = 'discord_quest_descriptions'
    __table_args__ = (
        PrimaryKeyConstraint('description_key', name='discord_quest_descriptions_pkey'),
    )

    description_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    text_: Mapped[str] = mapped_column('text', Text)


class EntityProperties(Base):
    __tablename__ = 'entity_properties'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='entity_properties_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    key: Mapped[str] = mapped_column(String)
    value: Mapped[Optional[str]] = mapped_column(Text)


class EntityStateMap(Base):
    __tablename__ = 'entity_state_map'
    __table_args__ = (
        PrimaryKeyConstraint('entity_access_key', 'access_code', name='entity_state_map_pkey'),
        Index('idx_esm_access_code', 'access_code')
    )

    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)


class FlagTemplates(Base):
    __tablename__ = 'flag_templates'
    __table_args__ = (
        PrimaryKeyConstraint('flag_key', name='flag_templates_pkey'),
    )

    flag_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    flag_category: Mapped[str] = mapped_column(String(50))
    flag_description: Mapped[str] = mapped_column(String(255))

    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='flag_templates')


class Inventory(Base):
    __tablename__ = 'inventory'
    __table_args__ = (
        PrimaryKeyConstraint('inventory_id', name='inventory_pkey'),
        Index('idx_inventory_character', 'character_id')
    )

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    item_id: Mapped[Optional[int]] = mapped_column(Integer)
    acquired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    equipped_items: Mapped[List['EquippedItems']] = relationship('EquippedItems', back_populates='inventory')


class ItemBase(Base):
    __tablename__ = 'item_base'
    __table_args__ = (
        PrimaryKeyConstraint('base_item_code', name='item_base_pkey'),
    )

    base_item_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    equip_slot: Mapped[str] = mapped_column(Text)
    base_durability: Mapped[int] = mapped_column(Integer)
    base_weight: Mapped[int] = mapped_column(Integer)

    template_modifier_defaults: Mapped[List['TemplateModifierDefaults']] = relationship('TemplateModifierDefaults', back_populates='item_base')


class Materials(Base):
    __tablename__ = 'materials'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='materials_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    prefix: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(Text)
    is_fragile: Mapped[Optional[bool]] = mapped_column(Boolean)
    strength_percentage: Mapped[Optional[int]] = mapped_column(Integer)


class ModifiersLibrary(Base):
    __tablename__ = 'modifiers_library'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='modifiers_library_pkey'),
        UniqueConstraint('access_modifier', name='modifiers_library_access_modifier_key'),
        UniqueConstraint('modifier_name', name='modifiers_library_modifier_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_modifier: Mapped[int] = mapped_column(Integer)
    modifier_name: Mapped[str] = mapped_column(Text)
    effect_description: Mapped[Optional[str]] = mapped_column(Text)

    suffixes: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod1_code]', back_populates='modifiers_library')
    suffixes_: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod2_code]', back_populates='modifiers_library_')
    suffixes1: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod3_code]', back_populates='modifiers_library1')
    suffixes2: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod4_code]', back_populates='modifiers_library2')
    template_modifier_defaults: Mapped[List['TemplateModifierDefaults']] = relationship('TemplateModifierDefaults', back_populates='modifiers_library')


class PlayerMagicAttack(Base):
    __tablename__ = 'player_magic_attack'
    __table_args__ = (
        PrimaryKeyConstraint('player_id', name='player_magic_attack_pkey'),
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    elemental_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    fire_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    water_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    air_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    earth_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    light_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    dark_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    gray_magic_power_bonus: Mapped[Optional[float]] = mapped_column(Double(53))


class PlayerMagicDefense(Base):
    __tablename__ = 'player_magic_defense'
    __table_args__ = (
        PrimaryKeyConstraint('player_id', name='player_magic_defense_pkey'),
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fire_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    water_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    air_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    earth_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    light_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    dark_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    gray_magic_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    magic_resistance_percent: Mapped[Optional[float]] = mapped_column(Double(53))


class PlayerPhysicalAttack(Base):
    __tablename__ = 'player_physical_attack'
    __table_args__ = (
        PrimaryKeyConstraint('player_id', name='player_physical_attack_pkey'),
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))


class PlayerPhysicalDefense(Base):
    __tablename__ = 'player_physical_defense'
    __table_args__ = (
        PrimaryKeyConstraint('player_id', name='player_physical_defense_pkey'),
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    physical_resistance_percent: Mapped[Optional[float]] = mapped_column(Double(53))


class QuestConditions(Base):
    __tablename__ = 'quest_conditions'
    __table_args__ = (
        PrimaryKeyConstraint('condition_id', name='quest_conditions_pkey'),
        UniqueConstraint('condition_key', name='quest_conditions_condition_key_key')
    )

    condition_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    condition_key: Mapped[str] = mapped_column(String(100))
    condition_name: Mapped[str] = mapped_column(String(255))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_conditions')


class QuestRequirements(Base):
    __tablename__ = 'quest_requirements'
    __table_args__ = (
        PrimaryKeyConstraint('requirement_id', name='quest_requirements_pkey'),
        UniqueConstraint('requirement_key', name='quest_requirements_requirement_key_key')
    )

    requirement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_key: Mapped[str] = mapped_column(String(100))
    requirement_name: Mapped[str] = mapped_column(String(255))
    requirement_value: Mapped[str] = mapped_column(String(255))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_requirements')


class QuestRewards(Base):
    __tablename__ = 'quest_rewards'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='quest_rewards_pkey'),
        UniqueConstraint('reward_key', name='quest_rewards_reward_key_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reward_key: Mapped[str] = mapped_column(String(100))
    reward_name: Mapped[str] = mapped_column(Text)
    reward_value: Mapped[int] = mapped_column(Integer)
    reward_type: Mapped[str] = mapped_column(Text)
    reward_description: Mapped[Optional[str]] = mapped_column(Text)

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_rewards')


class QuestTypes(Base):
    __tablename__ = 'quest_types'
    __table_args__ = (
        PrimaryKeyConstraint('type_id', name='quest_types_pkey'),
        UniqueConstraint('type_key', name='quest_types_type_key_key')
    )

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_key: Mapped[str] = mapped_column(String(100))
    type_name: Mapped[str] = mapped_column(String(255))
    difficulty_level: Mapped[str] = mapped_column(String(50), server_default=text("'medium'::character varying"))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_types')


class Quests(Base):
    __tablename__ = 'quests'
    __table_args__ = (
        PrimaryKeyConstraint('quest_id', name='quests_pkey'),
        UniqueConstraint('description_key', name='quests_description_key_key'),
        UniqueConstraint('quest_key', name='quests_quest_key_key'),
        UniqueConstraint('reward_key', name='quests_reward_key_key')
    )

    quest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_key: Mapped[int] = mapped_column(Integer)
    quest_name: Mapped[str] = mapped_column(String(255))
    description_key: Mapped[str] = mapped_column(String(100))
    reward_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), server_default=text("'inactive'::character varying"))
    progress_flag: Mapped[Optional[str]] = mapped_column(String(255), server_default=text('NULL::character varying'))

    quest_steps: Mapped[List['QuestSteps']] = relationship('QuestSteps', back_populates='quests')
    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='quests')


class Races(Base):
    __tablename__ = 'races'
    __table_args__ = (
        PrimaryKeyConstraint('race_id', name='races_pkey'),
    )

    race_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), server_default=text("''::character varying"))
    founder_id: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class Reputation(Base):
    __tablename__ = 'reputation'
    __table_args__ = (
        PrimaryKeyConstraint('reputation_id', name='reputation_pkey'),
    )

    reputation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reputation_value: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    reputation_status: Mapped[str] = mapped_column(String(50), server_default=text("'neutral'::character varying"))
    character_id: Mapped[Optional[int]] = mapped_column(Integer)
    faction_id: Mapped[Optional[int]] = mapped_column(Integer)


class Skills(Base):
    __tablename__ = 'skills'
    __table_args__ = (
        PrimaryKeyConstraint('skill_id', name='skills_pkey'),
        UniqueConstraint('skill_key', name='skills_skill_key_key')
    )

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_key: Mapped[str] = mapped_column(String(100))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    skill_group: Mapped[Optional[str]] = mapped_column(String(50))
    main_special: Mapped[Optional[str]] = mapped_column(String(50))
    secondary_special: Mapped[Optional[str]] = mapped_column(String(50))

    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='skill')
    progression_ticks: Mapped[List['ProgressionTicks']] = relationship('ProgressionTicks', back_populates='skill')
    skill_ability_unlocks: Mapped[List['SkillAbilityUnlocks']] = relationship('SkillAbilityUnlocks', back_populates='skills')
    skill_unlocks: Mapped[List['SkillUnlocks']] = relationship('SkillUnlocks', back_populates='skills')


class SpecialStatEffects(Base):
    __tablename__ = 'special_stat_effects'
    __table_args__ = (
        PrimaryKeyConstraint('stat_key', 'effect_field', name='special_stat_effects_pkey'),
    )

    stat_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    effect_field: Mapped[str] = mapped_column(String(50), primary_key=True)
    multiplier: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 4))
    description: Mapped[Optional[str]] = mapped_column(Text)


class StateEntities(Base):
    __tablename__ = 'state_entities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='state_entities_pkey'),
        UniqueConstraint('access_code', name='state_entities_access_code_key'),
        UniqueConstraint('code_name', name='state_entities_code_name_key'),
        Index('idx_state_entities_access_code', 'access_code'),
        Index('idx_state_entities_code_name', 'code_name'),
        Index('idx_state_entities_ui_type', 'ui_type')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer)
    code_name: Mapped[str] = mapped_column(Text)
    ui_type: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''::text"))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))


class WeaponTemplates(Base):
    __tablename__ = 'weapon_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='weapon_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer)
    suffix_code: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    rarity: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(Text)
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'))
    p_atk: Mapped[Optional[int]] = mapped_column(Integer)
    m_atk: Mapped[Optional[int]] = mapped_column(Integer)
    crit_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    crit_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    armor_penetration: Mapped[Optional[float]] = mapped_column(Double(53))
    durability: Mapped[Optional[int]] = mapped_column(Integer)
    accuracy: Mapped[Optional[float]] = mapped_column(Double(53))
    hp_steal_percent: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    effect_description: Mapped[Optional[str]] = mapped_column(Text)
    allowed_for_class: Mapped[Optional[str]] = mapped_column(Text)
    visual_asset: Mapped[Optional[str]] = mapped_column(Text)


class Worlds(Base):
    __tablename__ = 'worlds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='worlds_pkey'),
        UniqueConstraint('name', name='worlds_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String)
    is_static: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    discord_bindings: Mapped[List['DiscordBindings']] = relationship('DiscordBindings', back_populates='world')
    regions: Mapped[List['Regions']] = relationship('Regions', back_populates='world')
    state_entities_discord: Mapped[List['StateEntitiesDiscord']] = relationship('StateEntitiesDiscord', back_populates='world')


t_xp_tick_data = Table(
    'xp_tick_data', Base.metadata,
    Column('tick_id', Integer, nullable=False),
    Column('character_id', Integer),
    Column('skill_id', Integer),
    Column('xp_generated', Integer),
    Column('timestamp', DateTime, server_default=text('CURRENT_TIMESTAMP'))
)


class AutoSessions(Base):
    __tablename__ = 'auto_sessions'

    character_id = Column(Integer, ForeignKey('characters.character_id', ondelete="CASCADE"), primary_key=True)
    active_category = Column(Text, nullable=False)
    next_tick_at = Column(DateTime(timezone=True), nullable=False)  # ✅ Учли TIMESTAMPTZ
    last_tick_at = Column(DateTime(timezone=True), nullable=False)  # ✅ Учли TIMESTAMPTZ

    __table_args__ = (
        Index('idx_auto_sessions_next_tick_at', 'next_tick_at'),
    )


class CharacterSkills(Base):
    __tablename__ = 'character_skills'
    __table_args__ = (
        CheckConstraint("progress_state IN ('PLUS', 'PAUSE', 'MINUS')", name='character_skills_progress_state_check'),
        PrimaryKeyConstraint('character_id', 'skill_key', name='character_skills_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, ForeignKey('characters.character_id', ondelete='CASCADE'), primary_key=True)
    skill_key: Mapped[int] = mapped_column(Integer, ForeignKey('skills.skill_id', ondelete='CASCADE'), primary_key=True)  # ✅ Изменили с `String(100)` на `Integer`
    level: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    xp: Mapped[int] = mapped_column(BigInteger, server_default=text('0'))
    progress_state: Mapped[str] = mapped_column(String(10), server_default=text("'PLUS'"))

    skill: Mapped['Skills'] = relationship('Skills', back_populates='character_skills')



class CharacterStatus(Base):
    __tablename__ = 'character_status'

    player_id = Column(Integer, ForeignKey('characters.character_id', ondelete='CASCADE'), primary_key=True)
    current_health = Column(Integer)
    max_health = Column(Integer)
    current_energy = Column(Integer)
    crit_chance = Column(Double(53))
    crit_damage_bonus = Column(Double(53))
    anti_crit_chance = Column(Double(53))
    anti_crit_damage = Column(Double(53))
    dodge_chance = Column(Double(53))
    anti_dodge_chance = Column(Double(53))
    counter_attack_chance = Column(Double(53))
    parry_chance = Column(Double(53))
    block_chance = Column(Double(53))
    armor_penetration = Column(Double(53))
    physical_attack = Column(Double(53))
    magical_attack = Column(Double(53))
    magic_resistance = Column(Double(53))
    physical_resistance = Column(Double(53))
    mana_cost_reduction = Column(Double(53))
    regen_health_rate = Column(Double(53))
    energy_regeneration_bonus = Column(Double(53))
    energy_pool_bonus = Column(Integer)
    absorption_bonus = Column(Double(53))
    shield_value = Column(Double(53))
    shield_regeneration = Column(Double(53))


class Connections(Base):
    __tablename__ = 'connections'
    __table_args__ = (
        CheckConstraint("from_type::text = ANY (ARRAY['region'::character varying, 'subregion'::character varying]::text[])", name='connections_from_type_check'),
        CheckConstraint("to_type::text = ANY (ARRAY['region'::character varying, 'subregion'::character varying]::text[])", name='connections_to_type_check'),
        ForeignKeyConstraint(['type_id'], ['connection_types.id'], name='connections_type_id_fkey'),
        PrimaryKeyConstraint('id', name='connections_pkey'),
        Index('idx_connections_from', 'from_type', 'from_id'),
        Index('idx_connections_to', 'to_type', 'to_id'),
        Index('idx_connections_type_id', 'type_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    from_type: Mapped[str] = mapped_column(String)
    from_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    to_type: Mapped[str] = mapped_column(String)
    to_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    type_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    one_click: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    difficulty: Mapped[int] = mapped_column(Integer, server_default=text('1'))

    type: Mapped['ConnectionTypes'] = relationship('ConnectionTypes', back_populates='connections')


class DiscordBindings(Base):
    __tablename__ = 'discord_bindings'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='discord_bindings_world_id_fkey'),
        PrimaryKeyConstraint('guild_id', 'entity_access_key', name='discord_bindings_pkey'),
        Index('idx_discord_bindings_channel', 'channel_id')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    category_id: Mapped[Optional[str]] = mapped_column(String)
    channel_id: Mapped[Optional[str]] = mapped_column(String)

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='discord_bindings')
    applied_permissions: Mapped[List['AppliedPermissions']] = relationship('AppliedPermissions', back_populates='discord_bindings')


class EquippedItems(Base):
    __tablename__ = 'equipped_items'
    __table_args__ = (
        ForeignKeyConstraint(['inventory_id'], ['inventory.inventory_id'], ondelete='CASCADE', name='equipped_items_inventory_id_fkey'),
        PrimaryKeyConstraint('character_id', 'inventory_id', name='equipped_items_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    durability: Mapped[int] = mapped_column(Integer, server_default=text('100'))
    slot: Mapped[Optional[str]] = mapped_column(String(50))
    enchantment_effect: Mapped[Optional[dict]] = mapped_column(JSON)

    inventory: Mapped['Inventory'] = relationship('Inventory', back_populates='equipped_items')


class ProgressionTicks(Base):
    __tablename__ = 'progression_ticks'
    __table_args__ = (
        ForeignKeyConstraint(['skill_id'], ['skills.skill_id'], ondelete='CASCADE', name='progression_ticks_skill_id_fkey'),
        PrimaryKeyConstraint('tick_id', name='progression_ticks_pkey')
    )

    tick_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[Optional[int]] = mapped_column(Integer)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer)
    xp_generated: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    skill: Mapped[Optional['Skills']] = relationship('Skills', back_populates='progression_ticks')


class QuestSteps(Base):
    __tablename__ = 'quest_steps'
    __table_args__ = (
        ForeignKeyConstraint(['quest_key'], ['quests.quest_key'], name='quest_steps_quest_key_fkey'),
        PrimaryKeyConstraint('step_key', name='quest_steps_pkey')
    )

    step_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    quest_key: Mapped[int] = mapped_column(Integer)
    step_order: Mapped[int] = mapped_column(Integer)
    description_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    visibility_condition: Mapped[Optional[str]] = mapped_column(String(255))
    reward_key: Mapped[Optional[str]] = mapped_column(String(100))

    quests: Mapped['Quests'] = relationship('Quests', back_populates='quest_steps')
    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='quest_steps')


class QuestTemplatesMaster(Base):
    __tablename__ = 'quest_templates_master'
    __table_args__ = (
        ForeignKeyConstraint(['condition_key'], ['quest_conditions.condition_key'], name='quest_templates_master_condition_key_fkey'),
        ForeignKeyConstraint(['requirement_key'], ['quest_requirements.requirement_key'], name='quest_templates_master_requirement_key_fkey'),
        ForeignKeyConstraint(['reward_key'], ['quest_rewards.reward_key'], name='quest_templates_master_reward_key_fkey'),
        ForeignKeyConstraint(['type_key'], ['quest_types.type_key'], name='quest_templates_master_type_key_fkey'),
        PrimaryKeyConstraint('template_id', name='quest_templates_master_pkey'),
        UniqueConstraint('template_key', name='quest_templates_master_template_key_key')
    )

    template_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(String(100))
    type_key: Mapped[Optional[str]] = mapped_column(String(100))
    condition_key: Mapped[Optional[str]] = mapped_column(String(100))
    requirement_key: Mapped[Optional[str]] = mapped_column(String(100))
    reward_key: Mapped[Optional[str]] = mapped_column(String(100))

    quest_conditions: Mapped[Optional['QuestConditions']] = relationship('QuestConditions', back_populates='quest_templates_master')
    quest_requirements: Mapped[Optional['QuestRequirements']] = relationship('QuestRequirements', back_populates='quest_templates_master')
    quest_rewards: Mapped[Optional['QuestRewards']] = relationship('QuestRewards', back_populates='quest_templates_master')
    quest_types: Mapped[Optional['QuestTypes']] = relationship('QuestTypes', back_populates='quest_templates_master')


class Regions(Base):
    __tablename__ = 'regions'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='regions_world_id_fkey'),
        PrimaryKeyConstraint('id', name='regions_pkey'),
        UniqueConstraint('access_key', name='regions_access_key_key'),
        Index('idx_regions_access_key', 'access_key'),
        Index('idx_regions_name', 'name'),
        Index('idx_regions_world_id', 'world_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_key: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='regions')
    subregions: Mapped[List['Subregions']] = relationship('Subregions', back_populates='region')


class SkillAbilityUnlocks(Base):
    __tablename__ = 'skill_ability_unlocks'
    __table_args__ = (
        ForeignKeyConstraint(['ability_key'], ['abilities.ability_key'], ondelete='CASCADE', name='skill_ability_unlocks_ability_key_fkey'),
        ForeignKeyConstraint(['skill_key'], ['skills.skill_key'], ondelete='CASCADE', name='skill_ability_unlocks_skill_key_fkey'),
        PrimaryKeyConstraint('skill_key', 'level', 'ability_key', name='skill_ability_unlocks_pkey')
    )

    skill_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    level: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ability_key: Mapped[str] = mapped_column(String(100), primary_key=True)

    abilities: Mapped['Abilities'] = relationship('Abilities', back_populates='skill_ability_unlocks')
    skills: Mapped['Skills'] = relationship('Skills', back_populates='skill_ability_unlocks')


class SkillUnlocks(Base):
    __tablename__ = 'skill_unlocks'
    __table_args__ = (
        ForeignKeyConstraint(['skill_key'], ['skills.skill_key'], ondelete='CASCADE', name='skill_unlocks_skill_key_fkey'),
        PrimaryKeyConstraint('skill_key', 'rank', name='skill_unlocks_pkey')
    )

    skill_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    rank: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    xp_threshold: Mapped[int] = mapped_column(BigInteger)
    rank_name: Mapped[str] = mapped_column(String(100))

    skills: Mapped['Skills'] = relationship('Skills', back_populates='skill_unlocks')


class StateEntitiesDiscord(Base):
    __tablename__ = 'state_entities_discord'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='state_entities_discord_world_id_fkey'),
        PrimaryKeyConstraint('guild_id', 'access_code', name='state_entities_discord_pkey'),
        Index('idx_state_entities_discord_role_id', 'role_id'),
        Index('idx_state_entities_discord_updated_at', 'updated_at')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int] = mapped_column(BigInteger)
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='state_entities_discord')


class Suffixes(Base):
    __tablename__ = 'suffixes'
    __table_args__ = (
        ForeignKeyConstraint(['mod1_code'], ['modifiers_library.access_modifier'], name='suffixes_mod1_code_fkey'),
        ForeignKeyConstraint(['mod2_code'], ['modifiers_library.access_modifier'], name='suffixes_mod2_code_fkey'),
        ForeignKeyConstraint(['mod3_code'], ['modifiers_library.access_modifier'], name='suffixes_mod3_code_fkey'),
        ForeignKeyConstraint(['mod4_code'], ['modifiers_library.access_modifier'], name='suffixes_mod4_code_fkey'),
        PrimaryKeyConstraint('suffix_code', name='suffixes_pkey')
    )

    suffix_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    fragment: Mapped[str] = mapped_column(Text)
    is_for_weapon: Mapped[bool] = mapped_column(Boolean)
    is_for_armor: Mapped[bool] = mapped_column(Boolean)
    is_for_accessory: Mapped[bool] = mapped_column(Boolean)
    mod1_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod1_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod2_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod2_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod3_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod3_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod4_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod4_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)

    modifiers_library: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod1_code], back_populates='suffixes')
    modifiers_library_: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod2_code], back_populates='suffixes_')
    modifiers_library1: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod3_code], back_populates='suffixes1')
    modifiers_library2: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod4_code], back_populates='suffixes2')


class TemplateModifierDefaults(Base):
    __tablename__ = 'template_modifier_defaults'
    __table_args__ = (
        ForeignKeyConstraint(['access_modifier'], ['modifiers_library.access_modifier'], name='template_modifier_defaults_access_modifier_fkey'),
        ForeignKeyConstraint(['base_item_code'], ['item_base.base_item_code'], name='template_modifier_defaults_base_item_code_fkey'),
        PrimaryKeyConstraint('base_item_code', 'access_modifier', name='template_modifier_defaults_pkey')
    )

    base_item_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_modifier: Mapped[int] = mapped_column(Integer, primary_key=True)
    default_value: Mapped[decimal.Decimal] = mapped_column(Numeric)

    modifiers_library: Mapped['ModifiersLibrary'] = relationship('ModifiersLibrary', back_populates='template_modifier_defaults')
    item_base: Mapped['ItemBase'] = relationship('ItemBase', back_populates='template_modifier_defaults')


class TickEvents(Base):
    __tablename__ = 'tick_events'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_tick_events_character'),
        PrimaryKeyConstraint('id', name='tick_events_pkey'),
        Index('idx_tick_events_character', 'character_id'),
        Index('idx_tick_events_time', 'event_time')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    event_data: Mapped[dict] = mapped_column(JSONB)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('now()'))

    character: Mapped['Characters'] = relationship('Characters', back_populates='tick_events')


class TickSummary(Base):
    __tablename__ = 'tick_summary'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_tick_summary_character'),
        PrimaryKeyConstraint('id', name='tick_summary_pkey'),
        Index('idx_tick_summary_character_time', 'character_id', 'hour_block')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    hour_block: Mapped[datetime] = mapped_column(DateTime)
    tick_count: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(Text)
    summary_data: Mapped[dict] = mapped_column(JSONB)

    character: Mapped['Characters'] = relationship('Characters', back_populates='tick_summary')


class AppliedPermissions(Base):
    __tablename__ = 'applied_permissions'
    __table_args__ = (
        ForeignKeyConstraint(['guild_id', 'entity_access_key'], ['discord_bindings.guild_id', 'discord_bindings.entity_access_key'], ondelete='CASCADE', name='applied_permissions_guild_id_entity_access_key_fkey'),
        PrimaryKeyConstraint('guild_id', 'entity_access_key', 'access_code', 'target_type', 'target_id', 'role_id', name='applied_permissions_pkey'),
        Index('idx_applied_on_date', 'applied_at'),
        Index('idx_applied_on_role', 'guild_id', 'role_id'),
        Index('idx_applied_on_target', 'guild_id', 'target_type', 'target_id')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(Text, primary_key=True)
    target_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    discord_bindings: Mapped['DiscordBindings'] = relationship('DiscordBindings', back_populates='applied_permissions')


class QuestFlags(Base):
    __tablename__ = 'quest_flags'
    __table_args__ = (
        ForeignKeyConstraint(['flag_key_template'], ['flag_templates.flag_key'], ondelete='SET NULL', name='quest_flags_flag_key_template_fkey'),
        ForeignKeyConstraint(['quest_key'], ['quests.quest_key'], ondelete='CASCADE', name='quest_flags_quest_key_fkey'),
        ForeignKeyConstraint(['step_key'], ['quest_steps.step_key'], ondelete='CASCADE', name='quest_flags_step_key_fkey'),
        PrimaryKeyConstraint('flag_id', name='quest_flags_pkey'),
        UniqueConstraint('flag_key', name='quest_flags_flag_key_key')
    )

    flag_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flag_key: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)
    quest_key: Mapped[Optional[int]] = mapped_column(Integer)
    step_key: Mapped[Optional[str]] = mapped_column(String(100))
    flag_key_template: Mapped[Optional[str]] = mapped_column(String(100))

    flag_templates: Mapped[Optional['FlagTemplates']] = relationship('FlagTemplates', back_populates='quest_flags')
    quests: Mapped[Optional['Quests']] = relationship('Quests', back_populates='quest_flags')
    quest_steps: Mapped[Optional['QuestSteps']] = relationship('QuestSteps', back_populates='quest_flags')

class Subregions(Base):
    __tablename__ = 'subregions'
    __table_args__ = (
        ForeignKeyConstraint(['region_id'], ['regions.id'], ondelete='CASCADE', name='subregions_region_id_fkey'),
        PrimaryKeyConstraint('id', name='subregions_pkey'),
        UniqueConstraint('access_key', name='subregions_access_key_key'),
        Index('idx_subregions_access_key', 'access_key'),
        Index('idx_subregions_name', 'name'),
        Index('idx_subregions_peaceful', 'is_peaceful'),
        Index('idx_subregions_region_id', 'region_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    region_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_key: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    is_peaceful: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    description: Mapped[Optional[str]] = mapped_column(Text)

    region: Mapped['Regions'] = relationship('Regions', back_populates='subregions')



class CharacterExplorationChances(Base):
    __tablename__ = "character_exploration_chances"

    character_id = Column(Integer, primary_key=True)
    combat_chance = Column(Float, nullable=False)
    magic_chance = Column(Float, nullable=False)
    gathering_chance = Column(Float, nullable=False)
    last_updated = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP")

    __table_args__ = (
        Index("idx_exploration_chances", "combat_chance", "magic_chance", "gathering_chance"),
        Index("idx_last_updated", "last_updated"),
    )

class FinishHandler(Base):
    """Модель таблицы `finish_handlers` в SQLAlchemy."""
    
    __tablename__ = "finish_handlers"

    batch_id = Column(String, primary_key=True)  # Уникальный идентификатор пакета
    task_type = Column(String, nullable=False, index=True)  # ✅ Индекс по `task_type`
    completed_tasks = Column(Integer, default=0)  # Количество выполненных задач
    failed_tasks = Column(JSONB, nullable=True)  # 🔥 JSON с проваленными задачами
    status = Column(String, nullable=False, index=True)  # ✅ Итоговый статус (success, failed, partial)
    error_message = Column(Text, nullable=True)  # Сообщение об ошибке
    timestamp = Column(DateTime, default=datetime.now(timezone.utc), index=True)  # ✅ Корректный формат UTC
    processed_by_coordinator = Column(Boolean, default=False, index=True)  # ✅ Флаг обработки координатором

    # 🔹 Дополнительные индексы
    __table_args__ = (
        Index("idx_task_type", "task_type"),
        Index("idx_status", "status"),
        Index("idx_timestamp", "timestamp"),
        Index("idx_processed_coordinator", "processed_by_coordinator"),
    )
