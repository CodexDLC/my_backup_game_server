# --- Стандартная библиотека Python ---

from datetime import datetime, timezone # Для корректной работы с временными метками UTC
import decimal # Для работы с Numeric типами
import uuid # Для работы с UUID типами, если используются

from typing import Any, List, Optional, Dict # Общие типы для аннотаций

# --- Pydantic (если используется для валидации/сериализации моделей/схем) ---
# Если вы используете Pydantic для схем запросов/ответов FastAPI, эти импорты могут быть полезны.
# Если не используете, можете их удалить.


# --- SQLAlchemy Core (для определения столбцов и ограничений) ---
from sqlalchemy import (
    Column,                 # Классический способ определения столбца (для совместимости, хотя mapped_column предпочтительнее)
    DateTime,
    Identity,               # Тип данных для даты и времени
    Integer,                # Целочисленный тип
    String,                 # Строковый тип (VARCHAR)
    TEXT,                   # Текстовый тип (TEXT)
    Boolean,                # Логический тип
    Numeric,                # Числовой тип с фиксированной точностью (для валют, точных расчетов)
    Float,                  # Тип для чисел с плавающей запятой одинарной точности (REAL)
    Double,                 # Тип для чисел с плавающей запятой двойной точности (DOUBLE PRECISION)
    BigInteger,             # Большое целое число
    SmallInteger,           # Малое целое число
    JSON,                   # Общий JSON тип (для PostgreSQL лучше JSONB)
    ForeignKey,             # Для определения внешних ключей в Column
    Table,                  # Для определения таблиц без ORM (например, для ассоциативных таблиц многие-ко-многим)
    UniqueConstraint,       # Для определения уникальных ограничений
    PrimaryKeyConstraint,   # Для определения составных первичных ключей
    CheckConstraint,        # Для определения ограничений проверки
    ForeignKeyConstraint,   # Для определения составных внешних ключей
    Index,
    Uuid,                  # Для определения индексов
    text,                   # Для выполнения сырых SQL-выражений (например, для DEFAULT выражений)
    select,                 # Для построения SELECT запросов (для менеджеров)
    func                    # Для SQL-функций (например, func.now() для времени БД)
)

# --- SQLAlchemy ORM (для моделей и связей) ---
from sqlalchemy.orm import (
    DeclarativeBase,        # Базовый класс для всех ваших ORM-моделей
    Mapped,                 # Тип для аннотаций Mapped
    mapped_column,          # Функция для определения столбцов в Mapped стиле
    relationship,           # Для определения отношений между моделями
    sessionmaker,           # Для создания фабрик сессий (чаще в файле конфигурации БД)
    selectinload,           # Стратегия жадной загрузки для отношений (для менеджеров)
    joinedload,             # Альтернативная стратегия жадной загрузки
    subqueryload            # Еще одна стратегия жадной загрузки
)

# --- SQLAlchemy AsyncIO (для асинхронной работы) ---
from sqlalchemy.ext.asyncio import (
    AsyncSession,           # Асинхронная сессия
    create_async_engine     # Для создания асинхронного движка
)

# --- Диалекты PostgreSQL (если специфичные типы) ---
from sqlalchemy.dialects.postgresql import (
    JSONB,                  # Оптимизированный тип JSON для PostgreSQL
    UUID                    # Тип UUID для PostgreSQL
)

# --- Если используете alembic для миграций, эти импорты могут понадобиться в env.py или script.py.mako ---
# from alembic import op
# import sqlalchemy as sa

class Base(DeclarativeBase):
    pass


class Ability(Base):
    __tablename__ = 'abilities'

    ability_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ability_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    ability_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    required_skill_key: Mapped[Optional[str]] = mapped_column(ForeignKey('skills.skill_key', ondelete='SET NULL'))
    required_skill_level: Mapped[int] = mapped_column(Integer, default=0)
    required_stats: Mapped[Optional[dict]] = mapped_column(JSONB)
    required_items: Mapped[Optional[dict]] = mapped_column(JSONB)

    cost_type: Mapped[Optional[str]] = mapped_column(String(50))
    cost_amount: Mapped[int] = mapped_column(Integer, default=0)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, default=0)
    cast_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    effect_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    animation_key: Mapped[Optional[str]] = mapped_column(String(100))
    sfx_key: Mapped[Optional[str]] = mapped_column(String(100))
    vfx_key: Mapped[Optional[str]] = mapped_column(String(100))

    # Отношение к Skill, если это необходимо для получения информации о навыке
    skill_requirement: Mapped[Optional['Skills']] = relationship('Skills', back_populates='abilities_requiring_this_skill')

    # Отношение к character_abilities (если эта модель уже определена)
    # character_abilities: Mapped[List['CharacterAbility']] = relationship('CharacterAbility', back_populates='ability_definition')

    def __repr__(self):
        return f"<Ability(id={self.ability_id}, key='{self.ability_key}', name='{self.name}', type='{self.ability_type}')>"
    

class AccessoryTemplate(Base):
    __tablename__ = 'accessory_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='accessory_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer)
    suffix_code: Mapped[int] = mapped_column(Integer)
    accessory_name: Mapped[str] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy
    rarity: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy
    durability: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'))
    energy_pool_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    regen_energy_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    magic_defense_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    reflect_damage: Mapped[Optional[float]] = mapped_column(Double(53))
    damage_boost: Mapped[Optional[float]] = mapped_column(Double(53))
    excluded_bonus_type: Mapped[Optional[str]] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy
    effect_description: Mapped[Optional[str]] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy

    def __repr__(self):
        return f"<AccessoryTemplate(id={self.id}, name='{self.accessory_name}', rarity={self.rarity})>"




class AccountInfo(Base):
    __tablename__ = "account_info"

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True) # nullable=True, если email не обязателен
    avatar: Mapped[Optional[str]] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy
    locale: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False) # nullable=False, т.к. есть default
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False) # nullable=False, т.к. есть default
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False) # nullable=False, т.к. есть default
    linked_platforms: Mapped[Optional[dict]] = mapped_column(JSON, default={}, nullable=False) # Default {} для JSONB всегда должен быть not nullable
    auth_token: Mapped[Optional[str]] = mapped_column(TEXT) # Используем TEXT из SQLAlchemy
    
    # ✅ ИСПРАВЛЕНО: Используем datetime.now(timezone.utc) для времени с часовым поясом
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 🔹 Связь с персонажами (один аккаунт → несколько персонажей)
    # ✅ ИСПРАВЛЕНО: Имя класса "Character" (как ваша ORM-модель), back_populates="account_info"
    characters: Mapped[List["Character"]] = relationship("Character", back_populates="account_info")

    def __repr__(self):
        return f"<AccountInfo(account_id={self.account_id}, username={self.username}, status={self.status})>"




class ActiveQuests(Base):
    __tablename__ = 'active_quests'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='active_quests_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    quest_id: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), server_default=text("'active'::character varying"))
    current_step: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    quest_key: Mapped[Optional[str]] = mapped_column(String(100))
    flags_status: Mapped[Optional[dict]] = mapped_column(JSON)
    completion_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255))



class ArmorTemplate(Base):
    __tablename__ = 'armor_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='armor_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer, nullable=False) # Assuming these codes are always present
    suffix_code: Mapped[int] = mapped_column(Integer, nullable=False)
    armor_name: Mapped[str] = mapped_column(TEXT, nullable=False) # Use TEXT for long strings, assume name is required
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(TEXT, nullable=False)
    physical_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    durability: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False)
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'), nullable=False)
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'), nullable=False)
    magical_defense: Mapped[Optional[int]] = mapped_column(Integer)
    energy_regeneration_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_crit: Mapped[Optional[float]] = mapped_column(Double(53))
    dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    hp_percent: Mapped[Optional[float]] = mapped_column(Double(53))
    armor_boost: Mapped[Optional[int]] = mapped_column(Integer)
    armor_percent_boost: Mapped[Optional[float]] = mapped_column(Double(53))
    counter_attack: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_dodge: Mapped[Optional[float]] = mapped_column(Double(53))
    effect_description: Mapped[Optional[str]] = mapped_column(TEXT)
    allowed_for_class: Mapped[Optional[str]] = mapped_column(TEXT)
    visual_asset: Mapped[Optional[str]] = mapped_column(TEXT)
    
    # Using Python's datetime for UTC and timezone awareness, consistent with other models
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    # Added updated_at for consistency, common in templates tables
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return (f"<ArmorTemplate(id={self.id}, name='{self.armor_name}', "
                f"rarity={self.rarity}, phys_def={self.physical_defense})>")



class Bloodline(Base):
    __tablename__ = 'bloodlines'

    bloodline_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    inherent_bonuses: Mapped[dict] = mapped_column(JSONB, nullable=False) # JSONB маппится на Python dict
    rarity_weight: Mapped[int] = mapped_column(Integer, default=100)
    story_fragments: Mapped[Optional[dict]] = mapped_column(JSONB)

    characters: Mapped[List['Character']] = relationship('Character', back_populates='bloodline')
    def __repr__(self):
        return f"<Bloodline(id={self.bloodline_id}, name='{self.name}')>"
    

class CharacterExplorationChances(Base):
    __tablename__ = 'character_exploration_chances'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='character_exploration_chances_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    combat_chance: Mapped[float] = mapped_column(Double(53))
    magic_chance: Mapped[float] = mapped_column(Double(53))
    gathering_chance: Mapped[float] = mapped_column(Double(53))
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    



class DiscordBindings(Base):
    __tablename__ = 'discord_bindings'
    __table_args__ = (
        PrimaryKeyConstraint('guild_id', 'access_key', name='discord_bindings_pkey'),
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)  # 🔹 Оставляем, но убираем primary_key
    access_key: Mapped[str] = mapped_column(String, primary_key=True)  # ✅ Теперь ключ `access_key`
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    category_id: Mapped[Optional[str]] = mapped_column(String)
    channel_id: Mapped[Optional[str]] = mapped_column(String)




class EntityStateMap(Base):
    __tablename__ = 'entity_state_map'
    __table_args__ = (
        PrimaryKeyConstraint('entity_access_key', 'access_code', name='entity_state_map_pkey'),
    )

    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)


class EquippedItems(Base):
    __tablename__ = 'equipped_items'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='equipped_items_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_id: Mapped[int] = mapped_column(Integer)
    durability: Mapped[int] = mapped_column(Integer, server_default=text('100'))
    slot: Mapped[Optional[str]] = mapped_column(String(50))
    enchantment_effect: Mapped[Optional[dict]] = mapped_column(JSON)



class FinishHandler(Base):
    __tablename__ = 'finish_handlers'
    __table_args__ = (
        PrimaryKeyConstraint('batch_id', name='finish_handlers_pkey'),
        # Explicitly define indexes here
        Index('idx_processed_coordinator', 'processed_by_coordinator'),
        Index('idx_status', 'status'),
        Index('idx_task_type', 'task_type'),
        Index('idx_timestamp', 'timestamp'),
    )

    batch_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False) # Assuming task_type is always present
    status: Mapped[str] = mapped_column(String(50), nullable=False) # Assuming status is always present
    completed_tasks: Mapped[int] = mapped_column(Integer, server_default=text('0'), nullable=False) # Not optional if default is 0
    failed_tasks: Mapped[Optional[Dict]] = mapped_column(JSONB) # Use Dict for JSONB type hint
    error_message: Mapped[Optional[str]] = mapped_column(TEXT) # Use TEXT for potentially long error messages
    
    # Using Python's datetime for UTC and timezone awareness
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    processed_by_coordinator: Mapped[bool] = mapped_column(Boolean, server_default=text('false'), nullable=False)

    def __repr__(self):
        return (f"<FinishHandler(batch_id='{self.batch_id}', task_type='{self.task_type}', "
                f"status='{self.status}', completed_tasks={self.completed_tasks})>")



class Inventory(Base):
    __tablename__ = 'inventory'
    __table_args__ = (
        PrimaryKeyConstraint('inventory_id', name='inventory_pkey'),
    )

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    item_id: Mapped[Optional[int]] = mapped_column(Integer)
    acquired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class ItemBase(Base):
    """
    ORM модель для таблицы item_base.
    Хранит "метаданные 0 уровня" - базовые архетипы предметов.
    """
    __tablename__ = 'item_base'

    base_item_code = Column(String(255), primary_key=True) # Уникальный код архетипа
    category = Column(String(50), nullable=False) # Категория предмета
    properties_json = Column(JSONB, nullable=False, default={}) # Динамические свойства архетипа

    def __repr__(self):
        return f"<ItemBase(base_item_code='{self.base_item_code}', category='{self.category}')>"



class Material(Base):
    """
    ORM модель для таблицы materials.
    Хранит информацию о всех материалах (базовых и разломных).
    """
    __tablename__ = 'materials'

    material_code = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    material_category = Column(String(20), nullable=False)
    rarity_level = Column(Integer, nullable=True) # NULLABLE
    adjective = Column(String(255), nullable=False)
    color = Column(String(7), nullable=False)
    is_fragile = Column(Boolean, nullable=False)
    strength_percentage = Column(Float, nullable=False)

    def __repr__(self):
        return f"<Material(material_code='{self.material_code}', name='{self.name}')>"


class ModifierLibrary(Base):
    """
    ORM модель для таблицы modifier_library.
    Хранит централизованную библиотеку всех возможных модификаторов.
    """
    __tablename__ = 'modifier_library'

    modifier_code = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    effect_description = Column(TEXT, nullable=False)
    value_tiers = Column(JSONB, nullable=False) # Пример: {"1": 0.01, "2": 0.02, ...}
    randomization_range = Column(Float, nullable=False) # Пример: 0.3 для +/- 30%

    def __repr__(self):
        return f"<ModifierLibrary(modifier_code='{self.modifier_code}', name='{self.name}')>"
    


class PlayerMagicAttack(Base):
    __tablename__ = 'player_magic_attack'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='player_magic_attack_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
        PrimaryKeyConstraint('character_id', name='player_magic_defense_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
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
        PrimaryKeyConstraint('character_id', name='player_physical_attack_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))


class PlayerPhysicalDefense(Base):
    __tablename__ = 'player_physical_defense'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='player_physical_defense_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    physical_resistance_percent: Mapped[Optional[float]] = mapped_column(Double(53))


class QuestConditions(Base):
    __tablename__ = 'quest_conditions'
    __table_args__ = (
        PrimaryKeyConstraint('condition_id', name='quest_conditions_pkey'),
    )

    condition_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    condition_key: Mapped[str] = mapped_column(String(100))
    condition_name: Mapped[str] = mapped_column(String(255))


class QuestFlag(Base):
    __tablename__ = 'quest_flags'
    __table_args__ = (
        PrimaryKeyConstraint('flag_id', name='quest_flags_pkey'),
    )

    flag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # Assuming auto-incrementing ID
    flag_key: Mapped[str] = mapped_column(String(100), nullable=False) # flag_key is likely required
    value: Mapped[str] = mapped_column(TEXT, nullable=False) # value is likely required, can be longer text
    quest_key: Mapped[Optional[int]] = mapped_column(Integer)
    step_key: Mapped[Optional[str]] = mapped_column(String(100))
    flag_key_template: Mapped[Optional[str]] = mapped_column(String(100))

    def __repr__(self):
        return (f"<QuestFlag(flag_id={self.flag_id}, flag_key='{self.flag_key}', "
                f"value='{self.value}', quest_key={self.quest_key})>")

class QuestRequirements(Base):
    __tablename__ = 'quest_requirements'
    __table_args__ = (
        PrimaryKeyConstraint('requirement_id', name='quest_requirements_pkey'),
    )

    requirement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_key: Mapped[str] = mapped_column(String(100))
    requirement_name: Mapped[str] = mapped_column(String(255))
    requirement_value: Mapped[str] = mapped_column(String(255))


class QuestReward(Base):
    __tablename__ = 'quest_rewards'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='quest_rewards_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # Assuming auto-incrementing ID
    reward_key: Mapped[str] = mapped_column(String(100), nullable=False) # Reward key is likely required
    reward_name: Mapped[str] = mapped_column(TEXT, nullable=False) # Reward name is likely required, can be longer text
    reward_value: Mapped[int] = mapped_column(Integer, nullable=False) # Reward value is likely required
    reward_type: Mapped[str] = mapped_column(TEXT, nullable=False) # Reward type is likely required
    reward_description: Mapped[Optional[str]] = mapped_column(TEXT) # Reward description can be optional

    def __repr__(self):
        return (f"<QuestReward(id={self.id}, key='{self.reward_key}', "
                f"name='{self.reward_name}', value={self.reward_value}, type='{self.reward_type}')>")



class QuestSteps(Base):
    __tablename__ = 'quest_steps'

    step_key: Mapped[str] = mapped_column(String(100), primary_key=True)  # ✅ step_key — Primary Key
    quest_key: Mapped[int] = mapped_column(Integer)  # 🔄 ID квеста
    step_order: Mapped[int] = mapped_column(Integer)  # 🔄 Порядок шага
    description_key: Mapped[str] = mapped_column(String(100))  # 🔄 Ключ описания
    status: Mapped[str] = mapped_column(String(50))  # 🔄 Статус (`pending`, `completed`, `failed`)
    visibility_condition: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # 🔄 Условия видимости
    reward_key: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # 🔄 Ключ награды




class QuestTemplatesMaster(Base):
    __tablename__ = 'quest_templates_master'
    __table_args__ = (
        PrimaryKeyConstraint('template_id', name='quest_templates_master_pkey'),
    )

    template_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(String(100))
    type_key: Mapped[Optional[str]] = mapped_column(String(100))
    condition_key: Mapped[Optional[str]] = mapped_column(String(100))
    requirement_key: Mapped[Optional[str]] = mapped_column(String(100))
    reward_key: Mapped[Optional[str]] = mapped_column(String(100))


class QuestTypes(Base):
    __tablename__ = 'quest_types'
    __table_args__ = (
        PrimaryKeyConstraint('type_id', name='quest_types_pkey'),
    )

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_key: Mapped[str] = mapped_column(String(100))
    type_name: Mapped[str] = mapped_column(String(255))
    difficulty_level: Mapped[str] = mapped_column(String(50), server_default=text("'medium'::character varying"))


class Quests(Base):
    __tablename__ = 'quests'
    __table_args__ = (
        PrimaryKeyConstraint('quest_id', name='quests_pkey'),
    )

    quest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_key: Mapped[int] = mapped_column(Integer)
    quest_name: Mapped[str] = mapped_column(String(255))
    description_key: Mapped[str] = mapped_column(String(100))
    reward_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), server_default=text("'inactive'::character varying"))
    progress_flag: Mapped[Optional[str]] = mapped_column(String(255), server_default=text('NULL::character varying'))


class Races(Base):
    __tablename__ = 'races'
    __table_args__ = (
        PrimaryKeyConstraint('race_id', name='races_pkey'),
    )

    race_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race_name: Mapped[str] = mapped_column(String(100), server_default=text("''::character varying"))  # Было "name"
    founder_id: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))



class Regions(Base):
    __tablename__ = 'regions'

    # Note: If 'access_key' is the primary key, 'id' might not strictly need to be a primary key
    # or autoincrementing if it's generated by the server_default.
    # If both are PKs, consider using PrimaryKeyConstraint as you did in other tables.
    access_key: Mapped[str] = mapped_column(String(255), primary_key=True) # Assuming a reasonable string length
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), server_default=text('gen_random_uuid()'), nullable=False) # Use UUID from dialects
    world_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False) # Use UUID from dialects
    region_name: Mapped[str] = mapped_column(String(255), nullable=False) # Assuming a reasonable string length
    description: Mapped[Optional[str]] = mapped_column(TEXT) # Use TEXT for potentially long descriptions

    subregions: Mapped[List['Subregions']] = relationship(
        'Subregions',
        back_populates='parent_region',
        # <-- ДОБАВЬТЕ ЭТО: Явное условие объединения
        primaryjoin="Regions.access_key == Subregions.parent_access_key"
    )
    def to_dict(self):
        """Сериализация ORM-объекта в словарь"""
        # Improved serialization for UUIDs to convert them to strings
        return {
            column.name: str(getattr(self, column.name)) if isinstance(getattr(self, column.name), uuid.UUID) else getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self):
        return (f"<Region(access_key='{self.access_key}', id='{self.id}', "
                f"name='{self.region_name}', world_id='{self.world_id}')>")






class Reputation(Base):
    __tablename__ = 'reputation'
    __table_args__ = (
        PrimaryKeyConstraint('character_id', name='reputation_pkey'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reputation_value: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    reputation_status: Mapped[str] = mapped_column(String(50), server_default=text("'neutral'::character varying"))
    faction_id: Mapped[Optional[int]] = mapped_column(Integer)





class Skills(Base):
    __tablename__ = 'skills'

    skill_key = Column(String(50), primary_key=True, unique=True, nullable=False)
    skill_id = Column(Integer, autoincrement=True, unique=True) # skill_id не PK

    name = Column(String(100), nullable=False)
    description = Column(TEXT, nullable=True)

    stat_influence = Column(JSON, nullable=False) # Возможно, здесь лучше использовать JSONB из sqlalchemy.dialects.postgresql
    is_magic = Column(Boolean, nullable=False, default=False)
    rarity_weight = Column(Integer, nullable=False, default=100)
    category_tag = Column(String(50), nullable=False)
    role_preference_tag = Column(String(100), nullable=True)
    limit_group_tag = Column(String(100), nullable=True)

    creature_type_initial_skills: Mapped[List['CreatureTypeInitialSkill']] = relationship(
        'CreatureTypeInitialSkill',
        back_populates='skill_definition'
    )
    
    max_level = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<Skill(key='{self.skill_key}', name='{self.name}', id={self.skill_id})>"

    # Отношения
    abilities_requiring_this_skill: Mapped[List['Ability']] = relationship(
        'Ability',
        back_populates='skill_requirement'
    )

    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='skills')


class SpecialStatEffect(Base):
    __tablename__ = 'special_stat_effects'
    __table_args__ = (
        # Ограничение, чтобы для каждой характеристики и свойства был только один уникальный тип влияния
        UniqueConstraint('stat_key', 'affected_property', 'effect_type', name='uq_stat_property_effect_type'),
    )

    effect_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stat_key: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_property: Mapped[str] = mapped_column(String(100), nullable=False)
    effect_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False) # Используем float для Numeric в Python
    calculation_order: Mapped[int] = mapped_column(Integer, default=100)
    description: Mapped[Optional[str]] = mapped_column(TEXT)

    def __repr__(self):
        return (f"<SpecialStatEffect(id={self.effect_id}, stat='{self.stat_key}', "
                f"prop='{self.affected_property}', type='{self.effect_type}', value={self.value})>")



class StateEntity(Base):
    __tablename__ = 'state_entities'
    __table_args__ = (
        PrimaryKeyConstraint('access_code', name='state_entities_pkey'),
    )

    access_code: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # Assuming auto-incrementing
    code_name: Mapped[str] = mapped_column(TEXT, nullable=False) # Likely a required name
    ui_type: Mapped[str] = mapped_column(TEXT, nullable=False) # Likely a required UI type
    description: Mapped[Optional[str]] = mapped_column(TEXT, server_default=text("''::text"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text('true'), nullable=False) # Not optional if default is true

    discord_configs: Mapped[List['StateEntityDiscord']] = relationship('StateEntityDiscord', back_populates='state_entity')

    def __repr__(self):
        return (f"<StateEntity(access_code={self.access_code}, code_name='{self.code_name}', "
                f"ui_type='{self.ui_type}', is_active={self.is_active})>")

class StateEntityDiscord(Base):
    __tablename__ = 'state_entities_discord'
    __table_args__ = (
        PrimaryKeyConstraint('guild_id', 'world_id', 'access_code', name='state_entities_discord_pkey'),
        # Adding explicit foreign key constraint to StateEntity
        # Assuming 'access_code' in StateEntityDiscord references 'access_code' in StateEntities
        ForeignKeyConstraint(
            ['access_code'],
            ['state_entities.access_code'],
            name='fk_state_entities_discord_access_code',
            ondelete='CASCADE' # Or 'RESTRICT', 'SET NULL' based on your logic
        )
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True) # Part of composite PK and FK

    role_name: Mapped[str] = mapped_column(TEXT, nullable=False) # Role name is likely required
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False) # Role ID is likely required
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'), nullable=False) # Not optional if default is 0

    # Using Python's datetime for UTC and timezone awareness, consistent with other models
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    # Many-to-One relationship to StateEntity
    state_entity: Mapped['StateEntity'] = relationship(
        'StateEntity',
        primaryjoin="StateEntityDiscord.access_code == StateEntity.access_code",
        back_populates='discord_configs' # Add this back_populates to StateEntity if needed
    )

    def __repr__(self):
        return (f"<StateEntityDiscord(guild_id={self.guild_id}, world_id='{self.world_id}', "
                f"access_code={self.access_code}, role_name='{self.role_name}')>")



class Subregions(Base):
    __tablename__ = 'subregions'
    __table_args__ = (
        PrimaryKeyConstraint('access_key', name='subregions_pkey'),
        # Add a ForeignKeyConstraint if parent_access_key refers to Region.access_key
        ForeignKeyConstraint(
            ['parent_access_key'],
            ['regions.access_key'],
            name='fk_subregions_parent_region_access_key',
            ondelete='CASCADE' # Or 'RESTRICT', 'SET NULL' based on your desired behavior
        )
    )

    subregion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        server_default=text('gen_random_uuid()'),
        nullable=False # Assuming UUID is always generated
    )
    access_key: Mapped[str] = mapped_column(String(255), primary_key=True) # Assuming a reasonable string length
    access_code: Mapped[str] = mapped_column(String(255), nullable=False) # Marked as nullable=False per your note
    parent_access_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Can be NULL per your note
    subregion_name: Mapped[str] = mapped_column(String(255), nullable=False) # Assuming name is required
    is_peaceful: Mapped[bool] = mapped_column(Boolean, server_default=text('false'), nullable=False) # Not optional if default is false
    visibility: Mapped[str] = mapped_column(String(50), nullable=False) # Marked as nullable=False per your note, assuming reasonable length
    description: Mapped[Optional[str]] = mapped_column(TEXT) # For potentially long descriptions

    # Relationships (if you want to link to Region model)
    parent_region: Mapped[Optional['Regions']] = relationship('Regions', primaryjoin="Subregions.parent_access_key == Regions.access_key", back_populates='subregions')

    # ЭТА СТРОКА БЫЛА ИСТОЧНИКОМ ПРОБЛЕМЫ И ДОЛЖНА БЫТЬ УДАЛЕНА.
    # Она ошибочно создавала самоссылающееся отношение, которое вам не нужно.
    # subregions: Mapped[List['Subregions']] = relationship('Subregions', back_populates='parent_region')

    def to_dict(self):
        """Serializes the ORM object to a dictionary, converting UUIDs to strings."""
        return {
            column.name: str(getattr(self, column.name)) if isinstance(getattr(self, column.name), uuid.UUID) else getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self):
        return (f"<Subregion(access_key='{self.access_key}', name='{self.subregion_name}', "
                f"parent_key='{self.parent_access_key}', peaceful={self.is_peaceful})>")



class Suffix(Base):
    """
    ORM model for the suffixes table.
    Stores information about suffixes that can be applied to items.
    """
    __tablename__ = 'suffixes'

    suffix_code = Column(String(255), primary_key=True)
    fragment = Column(String(255), nullable=False)
    
    # --- ИСПРАВЛЕНО: Убраны кавычки вокруг имени атрибута ---
    # Python атрибут называется `group`
    # Первый аргумент Column("group", ...) - это имя колонки в БД
    group = Column("group", String(100), nullable=False, index=True)
    
    modifiers = Column(JSONB, nullable=False, default=lambda: [])

    def __repr__(self):
        # Этот метод уже был правильным, он использует self.group
        return f"<Suffix(suffix_code='{self.suffix_code}', group='{self.group}')>"




class TemplateModifierDefaults(Base):
    __tablename__ = 'template_modifier_defaults'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='template_modifier_defaults_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    base_item_code: Mapped[int] = mapped_column(Integer)
    access_modifier: Mapped[int] = mapped_column(Integer)
    default_value: Mapped[decimal.Decimal] = mapped_column(Numeric)


class WeaponTemplate(Base):
    __tablename__ = 'weapon_templates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='weapon_templates_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # Assuming ID is auto-incrementing
    base_item_code: Mapped[int] = mapped_column(Integer, nullable=False) # Assuming these codes are always present
    suffix_code: Mapped[int] = mapped_column(Integer, nullable=False)
    weapon_name: Mapped[str] = mapped_column(TEXT, nullable=False) # Weapon name is likely required
    rarity: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str] = mapped_column(TEXT, nullable=False)
    is_fragile: Mapped[bool] = mapped_column(Boolean, server_default=text('false'), nullable=False)
    strength_percentage: Mapped[float] = mapped_column(Double(53), server_default=text('0'), nullable=False)
    p_atk: Mapped[Optional[int]] = mapped_column(Integer) # Physical Attack
    m_atk: Mapped[Optional[int]] = mapped_column(Integer) # Magical Attack
    crit_chance: Mapped[Optional[float]] = mapped_column(Double(53)) # Critical Chance
    crit_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53)) # Critical Damage Bonus
    armor_penetration: Mapped[Optional[float]] = mapped_column(Double(53))
    durability: Mapped[Optional[int]] = mapped_column(Integer)
    accuracy: Mapped[Optional[float]] = mapped_column(Double(53))
    hp_steal_percent: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    effect_description: Mapped[Optional[str]] = mapped_column(TEXT)
    allowed_for_class: Mapped[Optional[str]] = mapped_column(TEXT)
    visual_asset: Mapped[Optional[str]] = mapped_column(TEXT)

    def __repr__(self):
        return (f"<WeaponTemplate(id={self.id}, name='{self.weapon_name}', "
                f"rarity={self.rarity}, p_atk={self.p_atk}, m_atk={self.m_atk})>")


class Worlds(Base):
    __tablename__ = 'worlds'
    __table_args__ = (
        PrimaryKeyConstraint('world_id', name='worlds_pkey'),  # ✅ Теперь PK — world_id
    )

    world_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))  # 🔄 Переименованный ID
    world_name: Mapped[str] = mapped_column(String)  # 🔄 Название мира
    is_static: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))  # 🔄 Статичный мир?
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=text('now()'))  # 🔄 Дата создания

        

class XpTickData(Base):
    __tablename__ = 'xp_tick_data'
    __table_args__ = (
        PrimaryKeyConstraint('tick_id', name='xp_tick_data_pkey'),
    )

    tick_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[Optional[int]] = mapped_column(Integer)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer)
    xp_generated: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


class Character(Base):
    __tablename__ = 'characters'

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    account_id: Mapped[int] = mapped_column(ForeignKey('account_info.account_id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String(100))

    bloodline_id: Mapped[Optional[int]] = mapped_column(ForeignKey('bloodlines.bloodline_id', ondelete='SET NULL'))
    # creature_type_id остается как внешний ключ, но без ORM-отношения
    creature_type_id: Mapped[int] = mapped_column(ForeignKey('creature_types.creature_type_id', ondelete='RESTRICT'), nullable=False)
    personality_id: Mapped[Optional[int]] = mapped_column(ForeignKey('personalities.personality_id', ondelete='SET NULL'))
    background_story_id: Mapped[Optional[int]] = mapped_column(ForeignKey('background_stories.story_id', ondelete='SET NULL'))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='offline', nullable=False)

    # Связи (Relationship) - ВСЕ РАСКОММЕНТИРОВАНЫ ИЛИ ДОБАВЛЕНЫ

    # Связь с AccountInfo (один аккаунт - много персонажей)
    account_info: Mapped['AccountInfo'] = relationship('AccountInfo', back_populates='characters')

    # Связь с Bloodline
    bloodline: Mapped[Optional['Bloodline']] = relationship('Bloodline', back_populates='characters')

    # Связь с Personality
    personality: Mapped[Optional['Personality']] = relationship('Personality', back_populates='characters')

    # Связь с BackgroundStory
    background_story: Mapped[Optional['BackgroundStory']] = relationship('BackgroundStory', back_populates='characters')

    # Связь с AutoSession (один-к-одному)
    auto_session: Mapped[Optional['AutoSession']] = relationship(
        'AutoSession',
        back_populates='character',
        uselist=False,
        primaryjoin="AutoSession.character_id == Character.character_id"
    )

    # Связь с CharacterSkills (один персонаж - много навыков)
    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='character')

    # Связь с CharacterSpecial (один-к-одному)
    special_stats: Mapped[Optional['CharacterSpecial']] = relationship(
        'CharacterSpecial',
        back_populates='character',
        uselist=False,
        primaryjoin="CharacterSpecial.character_id == Character.character_id"
    )

    # Связь с TickEvents (один персонаж - много событий тиков)
    tick_events: Mapped[List['TickEvents']] = relationship('TickEvents', back_populates='character')

    # Связь с TickSummary (один персонаж - много сводок тиков)
    tick_summaries: Mapped[List['TickSummary']] = relationship('TickSummary', back_populates='character')

    def __repr__(self):
        # Изменено __repr__ так, чтобы не обращаться к self.creature_type
        return (f"<Персонаж(id={self.character_id}, имя='{self.name}', "
                f"creature_type_id={self.creature_type_id}, " # Теперь используем только ID
                f"статус='{self.status}')>")



class AutoSession(Base):
    __tablename__ = 'auto_sessions'
    __table_args__ = (
        # The ForeignKeyConstraint is correctly defined for the relationship
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_character'),
        PrimaryKeyConstraint('character_id', name='auto_sessions_pkey'), # character_id is PK here, implying 1:1 or 0:1
        Index('idx_auto_sessions_next_tick_at', 'next_tick_at'),
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True) # This also serves as the foreign key

    active_category: Mapped[str] = mapped_column(TEXT, nullable=False) # Assuming an active category is always present
    
    # Using Python's datetime for UTC and timezone awareness, consistent with other models
    next_tick_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_tick_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Define the one-to-one relationship to Character
    # uselist=False indicates a one-to-one relationship
    character: Mapped['Character'] = relationship(
        'Character',
        back_populates='auto_session', # This back_populates should be defined in Character
        uselist=False, # Essential for one-to-one relationship
        # This relationship specifically links through the primary key of AutoSession
        primaryjoin="AutoSession.character_id == Character.character_id"
    )

    def __repr__(self):
        return (f"<AutoSession(character_id={self.character_id}, category='{self.active_category}', "
                f"next_tick_at={self.next_tick_at})>")



class CharacterSkills(Base):
    __tablename__ = 'character_skills'
    __table_args__ = (
        CheckConstraint("progress_state::text = ANY (ARRAY['PLUS'::character varying, 'PAUSE'::character varying, 'MINUS'::character varying]::text[])", name='character_skills_progress_state_check'),
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_character'),
        ForeignKeyConstraint(['skill_key'], ['skills.skill_key'], ondelete='CASCADE', name='fk_skill'),
        PrimaryKeyConstraint('character_id', 'skill_key', name='character_skills_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_key: Mapped[str] = mapped_column(String(50), ForeignKey('skills.skill_key'), primary_key=True) # ИСПРАВЛЕНО
    level: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    xp: Mapped[int] = mapped_column(BigInteger, server_default=text('0'))
    progress_state: Mapped[str] = mapped_column(String(10), server_default=text("'PLUS'::character varying"))

    character: Mapped['Character'] = relationship('Character', back_populates='character_skills')
    skills: Mapped['Skills'] = relationship('Skills', back_populates='character_skills')


class CharacterStatus(Character):
    __tablename__ = 'character_status'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_character'),
        PrimaryKeyConstraint('character_id', name='character_status_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_health: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    max_health: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    current_energy: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    crit_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    crit_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    anti_crit_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    anti_crit_damage: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    anti_dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    counter_attack_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    parry_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    block_chance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    armor_penetration: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    physical_attack: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    magical_attack: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    magic_resistance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    physical_resistance: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    mana_cost_reduction: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    regen_health_rate: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    energy_regeneration_bonus: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    energy_pool_bonus: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('0'))
    absorption_bonus: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    shield_value: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))
    shield_regeneration: Mapped[Optional[float]] = mapped_column(Double(53), server_default=text('0'))


class CharacterSpecial(Base):
    __tablename__ = 'characters_special'
    __table_args__ = (
        # The ForeignKeyConstraint is correctly defined for the relationship
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_character'),
        PrimaryKeyConstraint('character_id', name='characters_special_pkey') # character_id is PK here, implying 1:1 or 0:1
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True) # This also serves as the foreign key

    strength: Mapped[Optional[int]] = mapped_column(Integer)
    perception: Mapped[Optional[int]] = mapped_column(Integer)
    endurance: Mapped[Optional[int]] = mapped_column(Integer)
    agility: Mapped[Optional[int]] = mapped_column(Integer)
    intelligence: Mapped[Optional[int]] = mapped_column(Integer)
    charisma: Mapped[Optional[int]] = mapped_column(Integer)
    luck: Mapped[Optional[int]] = mapped_column(Integer)

    # Define the one-to-one relationship to Character
    # uselist=False indicates a one-to-one relationship
    character: Mapped['Character'] = relationship(
        'Character',
        back_populates='special_stats', # This back_populates should be defined in Character
        uselist=False, # Essential for one-to-one relationship
        primaryjoin="CharacterSpecial.character_id == Character.character_id"
    )

    def __repr__(self):
        return (f"<CharacterSpecial(character_id={self.character_id}, strength={self.strength}, "
                f"intelligence={self.intelligence}, luck={self.luck})>")


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

    character: Mapped['Character'] = relationship('Character', back_populates='tick_events')


class TickSummary(Base):
    __tablename__ = 'tick_summary'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='fk_tick_summary_character'),
        PrimaryKeyConstraint('id', name='tick_summary_pkey'),
        Index('idx_tick_summary_character_time', 'character_id', 'hour_block'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True) # Assuming ID is auto-incrementing
    character_id: Mapped[int] = mapped_column(Integer, nullable=False) # character_id is required
    
    # Using Python's datetime for UTC and timezone awareness, consistent with other models
    # hour_block should likely be a fixed point in time (e.g., start of the hour)
    hour_block: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    tick_count: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(TEXT, nullable=False) # Mode is likely required, using TEXT for flexibility
    summary_data: Mapped[Dict] = mapped_column(JSONB, nullable=False) # Summary data is likely required, using Dict for JSONB

    # Define the Many-to-One relationship to Character
    # Correct class name is 'Character', not 'Characters'
    character: Mapped['Character'] = relationship(
        'Character',
        back_populates='tick_summaries', # This back_populates should be defined in Character
        # Ensure it's a list on the Character side if one character has many summaries
    )

    def __repr__(self):
        return (f"<TickSummary(id={self.id}, character_id={self.character_id}, "
                f"hour_block={self.hour_block}, mode='{self.mode}')>")



class FlagTemplate(Base):
    __tablename__ = 'flag_templates'
    __table_args__ = (
        PrimaryKeyConstraint('flag_key', name='flag_templates_pkey'),
    )

    flag_key: Mapped[str] = mapped_column(String(50), primary_key=True) # Primary Key, unique flag key
    flag_category: Mapped[str] = mapped_column(String(50), nullable=False) # Flag category is likely required
    flag_description: Mapped[str] = mapped_column(TEXT, nullable=False) # Flag description is likely required, using TEXT for length

    def __repr__(self):
        return (f"<FlagTemplate(flag_key='{self.flag_key}', category='{self.flag_category}')>")



class CreatureTypeInitialSkill(Base):
    __tablename__ = 'creature_type_initial_skills'
    __table_args__ = (
        PrimaryKeyConstraint('creature_type_id', 'skill_key'), # Композитный первичный ключ
        # Внешние ключи будут определены через mapped_column и relationship
    )

    creature_type_id: Mapped[int] = mapped_column(ForeignKey('creature_types.creature_type_id'), nullable=False)
    skill_key: Mapped[str] = mapped_column(ForeignKey('skills.skill_key'), nullable=False) # skill_key здесь VARCHAR(50)
    initial_level: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # Связи с определениями
    creature_type_definition: Mapped['CreatureType'] = relationship(
        'CreatureType',
        back_populates='initial_skills'
    )
    skill_definition: Mapped['Skills'] = relationship('Skills', back_populates='creature_type_initial_skills')

    def __repr__(self):
        return (f"<CreatureTypeInitialSkill(creature_type_id={self.creature_type_id}, "
                f"skill_key='{self.skill_key}', initial_level={self.initial_level})>")






class CreatureType(Base):
    __tablename__ = 'creature_types'

    creature_type_id = Column(Integer, primary_key=True) # Без autoincrement
    name = Column(String(100), nullable=False)
    description = Column(TEXT, nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100), nullable=True)
    visual_tags = Column(JSONB, nullable=True)
    rarity_weight = Column(Integer, default=100)
    is_playable = Column(Boolean, default=False)


    initial_skills: Mapped[List['CreatureTypeInitialSkill']] = relationship(
        'CreatureTypeInitialSkill',
        back_populates='creature_type_definition'
    )

    def __repr__(self):
        return (f"<CreatureType(id={self.creature_type_id}, "
                f"name='{self.name}', "
                f"category='{self.category}', "
                f"subcategory='{self.subcategory}')>")

    def to_dict(self):
        # Если вы захотите включить начальные навыки в словарь CreatureType,
        # раскомментируйте или добавьте их здесь:
        # "initial_skills": [skill.to_dict() for skill in self.initial_skills]
        return {
            "creature_type_id": self.creature_type_id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "visual_tags": self.visual_tags,
            "rarity_weight": self.rarity_weight,
            "is_playable": self.is_playable,
        }



class Personality(Base):
    __tablename__ = 'personalities'

    personality_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    personality_group: Mapped[Optional[str]] = mapped_column(String(50))
    behavior_tags: Mapped[Optional[dict]] = mapped_column(JSONB)
    dialogue_modifiers: Mapped[Optional[dict]] = mapped_column(JSONB)
    combat_ai_directives: Mapped[Optional[dict]] = mapped_column(JSONB)
    quest_interaction_preferences: Mapped[Optional[dict]] = mapped_column(JSONB)
    trait_associations: Mapped[Optional[dict]] = mapped_column(JSONB)
    applicable_game_roles: Mapped[Optional[dict]] = mapped_column(JSONB)
    rarity_weight: Mapped[int] = mapped_column(Integer, default=100)
    ai_priority_level: Mapped[int] = mapped_column(Integer, default=50)

    characters: Mapped[List['Character']] = relationship('Character', back_populates='personality')
    def __repr__(self):
        return f"<Personality(id={self.personality_id}, name='{self.name}', group='{self.personality_group}')>"
    


class SkillExclusion(Base):
    __tablename__ = 'skill_exclusions'
    __table_args__ = (
        UniqueConstraint('group_name', name='uq_skill_exclusions_group_name'),
    )

    exclusion_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    exclusion_type: Mapped[str] = mapped_column(String(50), nullable=False)
    excluded_skills: Mapped[dict] = mapped_column(JSONB, nullable=False) # JSONB маппится на Python dict
    exclusion_effect: Mapped[Optional[dict]] = mapped_column(JSONB)

    def __repr__(self):
        return (f"<SkillExclusion(id={self.exclusion_id}, group='{self.group_name}', "
                f"type='{self.exclusion_type}')>")



class CharacterPool(Base):
    __tablename__ = 'character_pool'
    __table_args__ = (
        PrimaryKeyConstraint('character_pool_id', name='character_pool_pkey'),

        ForeignKeyConstraint(
            ['creature_type_id'],
            ['creature_types.creature_type_id'],
            ondelete='RESTRICT',
            name='fk_cp_creature_type'
        ),
        ForeignKeyConstraint(
            ['bloodline_id'],
            ['bloodlines.bloodline_id'],
            ondelete='SET NULL',
            name='fk_cp_bloodline'
        ),
        ForeignKeyConstraint(
            ['personality_id'],
            ['personalities.personality_id'],
            ondelete='SET NULL',
            name='fk_cp_personality'
        ),
        ForeignKeyConstraint(
            ['background_story_id'],
            ['background_stories.story_id'],
            ondelete='SET NULL',
            name='fk_cp_background_story'
        ),

        Index('idx_character_pool_status', 'status'),
        Index('idx_character_pool_creature_type', 'creature_type_id'),
        Index('idx_character_pool_rarity_score', 'rarity_score'),
    )

    character_pool_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    creature_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bloodline_id: Mapped[Optional[int]] = mapped_column(Integer)
    personality_id: Mapped[Optional[int]] = mapped_column(Integer)
    background_story_id: Mapped[Optional[int]] = mapped_column(Integer)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    base_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    visual_appearance_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    initial_skill_levels: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)   
    
    initial_role_name: Mapped[Optional[str]] = mapped_column(String(100)) # Поле, добавленное в прошлый раз
    # ▼▼▼ НОВОЕ ПОЛЕ ▼▼▼
    # Сохраняем quality_level, использованный при генерации.
    # Тип String, так как в логах у вас было 'BASIC_QUALITY'.
    # Добавляем index=True, так как вы будете по нему фильтровать.
    quality_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default=text("'available'"))
    is_unique: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    rarity_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('100'))
    
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    death_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self):
        return (f"<CharacterPool(id={self.character_pool_id}, name='{self.name} {self.surname or ''}', "
                f"type_id={self.creature_type_id}, status='{self.status}')>")
    


class BackgroundStory(Base):
    __tablename__ = 'background_stories'

    story_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    short_description = Column(TEXT, nullable=True)

    stat_modifiers = Column(JSONB, nullable=True)
    skill_affinities = Column(JSONB, nullable=True)
    initial_inventory_items = Column(JSONB, nullable=True) # JSONB: {"item_id_1": 1, "item_id_2": 3}
    starting_location_tags = Column(JSONB, nullable=True)

    lore_fragments = Column(JSONB, nullable=True)
    potential_factions = Column(JSONB, nullable=True)

    rarity_weight = Column(Integer, default=100)

    characters: Mapped[List['Character']] = relationship('Character', back_populates='background_story')

    def __repr__(self):
        return f"<BackgroundStory(id={self.story_id}, name='{self.name}')>"

class CharacterStarterInventory(Base):
    __tablename__ = 'character_starter_inventories'

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(TEXT, nullable=True)
    items = Column(JSONB, nullable=False) # JSONB, описывающий предметы и их количество

    # Возможно, обратная связь с CharacterInventoryRule, если потребуется
    # rules: Mapped[List["CharacterInventoryRule"]] = relationship(
    #     "CharacterInventoryRule", back_populates="inventory"
    # )

    def __repr__(self):
        return f"<CharacterStarterInventory(id={self.inventory_id}, name='{self.name}')>"


class CharacterInventoryRule(Base):
    __tablename__ = 'character_inventory_rules'

    rule_id = Column(Integer, primary_key=True, autoincrement=True)
    quality_level = Column(String(100), nullable=False) # Например, "STANDARD_QUALITY"
    role_name = Column(String(100), nullable=True) # Например, "WARRIOR", может быть NULL
    inventory_id = Column(Integer, ForeignKey('character_starter_inventories.inventory_id'), nullable=False)
    weight = Column(Integer, default=100)

    # Отношение к CharacterStarterInventory
    inventory = relationship("CharacterStarterInventory", backref="rules")

    def __repr__(self):
        return f"<CharacterInventoryRule(id={self.rule_id}, quality='{self.quality_level}', role='{self.role_name}')>"
    

class InventoryRuleGenerator(Base):
    __tablename__ = 'inventory_rule_generator'

    rule_key = Column(String(150), primary_key=True)
    
    # --- ИЗМЕНЕНИЕ ---
    # Заменяем autoincrement=True на явное указание Identity.
    # Это точно скажет Alembic, какую конструкцию мы хотим видеть в базе.
    rule_id = Column(Integer, Identity(always=False), unique=True, nullable=False)
    
    # ... остальные поля ...
    description = Column(TEXT, nullable=True)
    quality_level = Column(Integer, nullable=False, index=True)
    weight = Column(Integer, default=100, nullable=False)
    activation_conditions = Column(JSONB, nullable=False)
    generation_rules = Column(JSONB, nullable=False)

    def __repr__(self):
        return f"<InventoryRuleGenerator(rule_key='{self.rule_key}', rule_id={self.rule_id})>"
    
    
    
class DiscordQuestDescription(Base): # Используем PascalCase для имени класса
    __tablename__ = 'discord_quest_descriptions' # Имя таблицы, как в вашей схеме

    description_key = Column(String(100), primary_key=True, unique=True, nullable=False) # Кей как Primary Key
    text_ = Column(TEXT, nullable=False) # Текст описания, может быть многострочным

    def __repr__(self):
        return f"<DiscordQuestDescription(key='{self.description_key}', text_preview='{self.text_[:50]}...')>"



class StaticItemTemplate(Base):
    """
    ORM модель для таблицы static_item_templates.
    Хранит шаблоны для всех неэкипируемых предметов.
    """
    __tablename__ = 'static_item_templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    item_code = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=True) # NULLABLE
    inventory_size = Column(String(10), nullable=False)
    stackable = Column(Boolean, nullable=False, default=False)
    max_stack_size = Column(Integer, nullable=False, default=1)
    base_value = Column(Integer, nullable=False, default=0)
    icon_url = Column(String(255), nullable=True) # NULLABLE
    description = Column(TEXT, nullable=True) # NULLABLE
    properties_json = Column(JSONB, nullable=False, default={}) # JSONB

    def __repr__(self):
        return f"<StaticItemTemplate(item_code='{self.item_code}', display_name='{self.display_name}')>"


class EquipmentTemplate(Base):
    """
    ORM model for the equipment_templates table.
    Stores templates for all equippable items (weapons, armor, apparel, accessories).
    """
    __tablename__ = 'equipment_templates'

    template_id = Column(Integer, primary_key=True, autoincrement=True)
    item_code = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    sub_category = Column(String(50), nullable=False)
    equip_slot = Column(String(50), nullable=False)
    inventory_size = Column(String(10), nullable=False)
    
    material_code = Column(String(255), nullable=False)
    suffix_code = Column(String(255), nullable=True) # NULLABLE
    
    base_modifiers_json = Column(JSONB, nullable=False, default={})
    
    quality_tier = Column(String(50), nullable=True) # NULLABLE, specific to apparel
    
    rarity_level = Column(Integer, nullable=False)
    
    icon_url = Column(String(255), nullable=True) # NULLABLE
    description = Column(TEXT, nullable=True) # NULLABLE

    def __repr__(self):
        return f"<EquipmentTemplate(item_code='{self.item_code}', display_name='{self.display_name}')>"
    

class InstancedItem(Base):
    """
    ORM модель для таблицы instanced_items.
    Хранит уникальные экземпляры предметов, выданных игрокам или монстрам.
    """
    __tablename__ = 'instanced_items'

    instance_id = Column(Integer, primary_key=True, autoincrement=True)
    
    template_id = Column(Integer, nullable=False) # ID шаблона, из которого создан экземпляр
    is_equippable = Column(Boolean, nullable=False) # Флаг: True если экипируемый, False если статический
    
    owner_id = Column(Integer, nullable=False) # ID владельца (character_id, monster_id, container_id и т.д.)
    owner_type = Column(String(20), nullable=False) # Тип владельца ('CHARACTER', 'MONSTER', 'CONTAINER', 'VENDOR', 'AUCTION_HOUSE')
    location_type = Column(String(50), nullable=False) # Местоположение ('INVENTORY', 'EQUIPPED', 'STORAGE', 'VENDOR_STOCK', 'AUCTION_LISTING', 'CORPSE_LOOT')
    location_slot = Column(String(50), nullable=True) # Слот экипировки или инвентаря (NULLABLE)

    final_modifiers_json = Column(JSONB, nullable=False, default={}) # Финальные, рандомизированные модификаторы
    
    display_name = Column(String(255), nullable=False) # Отображаемое имя предмета (дублируется для быстрого доступа)
    item_category = Column(String(50), nullable=False) # Категория предмета (дублируется)
    item_sub_category = Column(String(50), nullable=True) # Субкатегория предмета (NULLABLE)
    inventory_size = Column(String(10), nullable=True) # Размер в инвентаре (NULLABLE)

    current_durability = Column(Integer, nullable=True) # Текущая прочность экземпляра (NULLABLE)
    current_stack_size = Column(Integer, nullable=False, default=1) # Текущий размер стака
    
    def __repr__(self):
        return f"<InstancedItem(instance_id={self.instance_id}, display_name='{self.display_name}', owner_type='{self.owner_type}', owner_id={self.owner_id})>"


class EliteMonster(Base):
    """
    ORM модель для таблицы elite_monsters.
    Хранит информацию об элитных монстрах, которые получили экипировку убитых игроков.
    """
    __tablename__ = 'elite_monsters'

    monster_instance_id = Column(Integer, primary_key=True, autoincrement=True)
    monster_template_id = Column(Integer, nullable=False) # ID базового шаблона монстра
    
    display_name = Column(String(255), nullable=False)
    current_location = Column(String(255), nullable=False)
    last_player_killed_id = Column(Integer, nullable=True) # ID последнего убитого игрока (NULLABLE)
    killed_players_count = Column(Integer, nullable=False, default=0) # Счетчик убитых игроков
    
    current_status = Column(String(50), nullable=False, default='IDLE_IN_POOL') # Статус монстра
    killed_by_info_json = Column(JSONB, nullable=False, default={}) # Информация об убийце
    
    unique_modifiers_json = Column(JSONB, nullable=False, default={}) # Уникальные модификаторы элитного монстра
    
    is_active = Column(Boolean, nullable=False, default=True)
    spawn_priority = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<EliteMonster(monster_instance_id={self.monster_instance_id}, display_name='{self.display_name}', current_status='{self.current_status}')>"
    
    
    
    