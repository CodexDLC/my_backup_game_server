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
    """
    Базовый класс для всех ORM-моделей, предоставляющий общий функционал.
    """
    pass

    def to_dict(self) -> Dict[str, Any]: # <--- ДОБАВЬТЕ ЭТОТ МЕТОД
        """
        Преобразует объект ORM-модели в словарь Python.
        Автоматически преобразует UUID и datetime в строки для MsgPack/JSON сериализации.
        """
        data = {}
        # Проходим по всем колонкам таблицы, ассоциированной с этой моделью
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, uuid.UUID):
                data[column.name] = str(value)
            elif isinstance(value, datetime):
                # datetime можно преобразовать в ISO-формат для совместимости
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data


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
    

class AccountGameData(Base):
    __tablename__ = 'account_game_data'

    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('account_info.account_id', ondelete='CASCADE'), primary_key=True)
    
    # ✅ ИЗМЕНЕНО: Теперь внешний ключ ссылается на fragment_key (VARCHAR)
    past_life_fragment_key: Mapped[Optional[str]] = mapped_column(ForeignKey('past_life_fragments.fragment_key', ondelete='SET NULL'))
    
    characters_json: Mapped[dict] = mapped_column(JSONB, default=lambda: [])
    account_cards_data: Mapped[dict] = mapped_column(JSONB, default=lambda: {})
    shard_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey('game_shards.discord_guild_id', ondelete='SET NULL'), nullable=True)
    
    last_login_game: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    total_playtime_seconds: Mapped[int] = mapped_column(BigInteger, default=0)

    # Отношение один-к-одному с AccountInfo
    account_info: Mapped['AccountInfo'] = relationship('AccountInfo', back_populates='game_data', uselist=False)
    
    # ✅ ИЗМЕНЕНО: Отношение к PastLifeFragment, привязанное к новому ключу
    past_life_fragment: Mapped[Optional['PastLifeFragment']] = relationship('PastLifeFragment', back_populates='accounts_game_data')

    def __repr__(self):
        return f"<AccountGameData(account_id={self.account_id}, shard_id='{self.shard_id}', fragment_key='{self.past_life_fragment_key}')>"


class AccountInfo(Base):
    __tablename__ = "account_info"

    account_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(TEXT)
    locale: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    twofa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    linked_platforms: Mapped[Optional[dict]] = mapped_column(JSON, default={}, nullable=False)
    auth_token: Mapped[Optional[str]] = mapped_column(TEXT)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # 🔹 Связь с персонажами (один аккаунт → несколько персонажей)
    characters: Mapped[List["Character"]] = relationship("Character", back_populates="account_info")

    # Связь один-к-одному с AccountGameData
    game_data: Mapped[Optional['AccountGameData']] = relationship('AccountGameData', back_populates='account_info', uselist=False)

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
    access_code: Mapped[str] = mapped_column(String(50), primary_key=True, unique=True, nullable=False, index=True)
    code_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ui_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(True), default=lambda: datetime.now(timezone.utc))
    def __repr__(self):
        return (f"<StateEntity(access_code='{self.access_code}', "
                f"code_name='{self.code_name}', ui_type='{self.ui_type}', "
                f"is_active={self.is_active})>")









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

    character_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    account_id: Mapped[int] = mapped_column(ForeignKey('account_info.account_id', ondelete='CASCADE'), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String(100))

    # ✅ НОВОЕ: Добавляем поле gender
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Можно сделать nullable=False и добавить default, если пол всегда известен

    clan_id: Mapped[Optional[int]] = mapped_column(ForeignKey('bloodlines_clan.clan_id', ondelete='SET NULL'))
    creature_type_id: Mapped[int] = mapped_column(ForeignKey('creature_types.creature_type_id', ondelete='RESTRICT'), nullable=False)
    personality_id: Mapped[Optional[int]] = mapped_column(ForeignKey('personalities.personality_id', ondelete='SET NULL'))
    background_story_id: Mapped[Optional[int]] = mapped_column(ForeignKey('background_stories.story_id', ondelete='SET NULL'))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='offline', nullable=False)

    # Связи (Relationship)
    account_info: Mapped['AccountInfo'] = relationship('AccountInfo', back_populates='characters')

    clan: Mapped[Optional['Clan']] = relationship('Clan', back_populates='characters')

    personality: Mapped[Optional['Personality']] = relationship('Personality', back_populates='characters')

    background_story: Mapped[Optional['BackgroundStory']] = relationship('BackgroundStory', back_populates='characters')

    auto_session: Mapped[Optional['AutoSession']] = relationship(
        'AutoSession',
        back_populates='character',
        uselist=False,
        primaryjoin="AutoSession.character_id == Character.character_id"
    )

    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='character')

    special_stats: Mapped[Optional['CharacterSpecial']] = relationship(
        'CharacterSpecial',
        back_populates='character',
        uselist=False,
        primaryjoin="CharacterSpecial.character_id == Character.character_id"
    )

    def __repr__(self):
        return (f"<Персонаж(id={self.character_id}, имя='{self.name}', "
                f"gender='{self.gender}', " # Добавлено gender в repr
                f"creature_type_id={self.creature_type_id}, "
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
        # ForeignKeyConstraint на bloodline_id УДАЛЕН отсюда
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
   
    personality_id: Mapped[Optional[int]] = mapped_column(Integer)
    background_story_id: Mapped[Optional[int]] = mapped_column(Integer)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    surname: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    base_stats: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    visual_appearance_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB)
    
    initial_skill_levels: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)   
    
    initial_role_name: Mapped[Optional[str]] = mapped_column(String(100))
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
    
    
    
class DataVersion(Base):
    """
    Модель для хранения хэш-сумм (версий) для различных наборов
    справочных данных (например, для таблиц 'materials', 'skills' и т.д.).
    """
    __tablename__ = 'data_versions'

    # Имя таблицы или логической группы данных, например 'materials' или 'item_base_templates'
    table_name = Column(String, primary_key=True, comment="Имя таблицы или логической группы данных")

    # Рассчитанная хэш-сумма данных (SHA256)
    data_hash = Column(String, nullable=False, comment="Хэш-сумма данных (SHA256)")

    def __repr__(self):
        return f"<DataVersion(table_name='{self.table_name}', data_hash='{self.data_hash[:8]}...')>"
    
    
    
class PastLifeFragment(Base):
    __tablename__ = 'past_life_fragments'

    # ✅ ИЗМЕНЕНО: fragment_key как строковый PK
    fragment_key: Mapped[str] = mapped_column(String(100), primary_key=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    inherent_bonuses: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rarity_weight: Mapped[int] = mapped_column(Integer, default=100)
    story_fragments: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Обратное отношение для AccountGameData
    # Обновлено: 'AccountGameData' будет ссылаться через fragment_key
    accounts_game_data: Mapped[List['AccountGameData']] = relationship('AccountGameData', back_populates='past_life_fragment')

    def __repr__(self):
        # Обновлен repr для использования fragment_key
        return f"<PastLifeFragment(key='{self.fragment_key}', name='{self.name}')>"
    
    
class Clan(Base): # Новое имя класса для "клановой" сущности
    __tablename__ = 'bloodlines_clan' # Имя таблицы в БД

    clan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    clan_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(TEXT)
    leader_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey('account_info.account_id', ondelete='SET NULL'))
    founding_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='active', nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reputation: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    assets_json: Mapped[dict] = mapped_column(JSONB, default=lambda: {}, nullable=False)
    policies_json: Mapped[dict] = mapped_column(JSONB, default=lambda: {}, nullable=False)

    # Отношение к лидеру аккаунта
    leader_account: Mapped[Optional['AccountInfo']] = relationship('AccountInfo') # Если не нужно обратное отношение в AccountInfo

    # Отношение к персонажам, принадлежащим этому клану
    characters: Mapped[List['Character']] = relationship('Character', back_populates='clan')

    def __repr__(self):
        return f"<Clan(id={self.clan_id}, name='{self.clan_name}', leader_id={self.leader_account_id})>"
    
    
class UsedCharacterArchive(Base):
    """
    Универсальная таблица для отслеживания шаблонов, выданных из пула
    различным игровым сущностям (игрокам, NPC и т.д.).
    """
    __tablename__ = 'used_characters_archive'
    
    archive_id = Column(Integer, primary_key=True)
    original_pool_id = Column(Integer, nullable=False, unique=True)
    
    # Универсальные поля для связи
    linked_entity_id = Column(Integer, nullable=False, index=True)
    activation_type = Column(String(50), nullable=False) # 'PLAYER', 'NPC_COMPANION', etc.
    
    # Статус жизненного цикла
    lifecycle_status = Column(String(50), nullable=False, default='ACTIVE')
    
    # Опциональная ссылка на аккаунт (только для игроков)
    linked_account_id = Column(Integer, nullable=True)
    
    simplified_pool_data = Column(JSON)
    archived_at = Column(DateTime(timezone=True), server_default=func.now())
    



class DiscordEntity(Base):
    """
    Универсальная таблица для хранения ВСЕХ сущностей Discord:
    ролей, каналов, категорий и т.д.
    Тип сущности определяется полем 'entity_type'.
    """
    __tablename__ = 'discord_entities'
    
    # ИСПРАВЛЕНИЕ: Добавляем составной уникальный ключ на guild_id и access_code
    # И убираем unique=True из определения колонки access_code ниже.
    __table_args__ = (
        UniqueConstraint('guild_id', 'discord_id', name='uq_guild_discord_id'),
        UniqueConstraint('guild_id', 'access_code', name='uq_guild_access_code'), # <--- НОВОЕ: ЭТО РЕШЕНИЕ
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    discord_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    permissions: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # --- ПОЛЕ, ПЕРЕНЕСЕННОЕ ИЗ STATE_ENTITIES_DISCORD ---
    # Важнейшее поле для связи роли с игровой логикой.
    # Для каналов и категорий будет NULL.
    # ИСПРАВЛЕНИЕ: unique=True УДАЛЕНО отсюда, так как уникальность теперь в __table_args__
    access_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True) 
    
    # --- Общие поля ---
    created_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (f"<DiscordEntity(id={self.id}, guild_id={self.guild_id}, "
                f"discord_id={self.discord_id}, name='{self.name}', "
                f"entity_type='{self.entity_type}', access_code='{self.access_code}')>")



class GameShard(Base):
    """
    ORM-модель для хранения информации о игровых шарадах (Discord-серверах).
    """
    __tablename__ = 'game_shards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    shard_name = Column(String(100), unique=True, nullable=False)
    discord_guild_id = Column(BigInteger, unique=True, nullable=False)
    current_players = Column(Integer, default=0, nullable=False)
    max_players = Column(Integer, default=200, nullable=False) # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
    is_admin_enabled = Column(Boolean, default=False, nullable=False) # Админский мастер-переключатель
    is_system_active = Column(Boolean, default=False, nullable=False) # Серверный флаг активности/сна
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    def __repr__(self):
        return (
            f"<GameShard(id={self.id}, name='{self.shard_name}', "
            f"guild_id={self.discord_guild_id}, players={self.current_players}, "
            f"admin_enabled={self.is_admin_enabled}, system_active={self.is_system_active})>"
        )
        

class GameLocation(Base):
    """
    Универсальная модель для всех сущностей игрового мира (кварталов, улиц,
    зданий, комнат, шлюзов). Поддерживает иерархическую вложенность
    и панорамную модель навигации.
    """
    __tablename__ = 'game_locations'

    # --- Основные Идентификаторы ---
    access_key: Mapped[str] = mapped_column(
        String(255), primary_key=True,
        comment="Иерархический ID 'X-XX-YY-ZZZ'. Главный ключ для связей."
    )
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), server_default=text('gen_random_uuid()'), unique=True,
        comment="Уникальный внутренний ID записи в базе."
    )
    parent_id: Mapped[Optional[str]] = mapped_column(
        String(255), ForeignKey('game_locations.access_key', ondelete='CASCADE'),
        nullable=True, comment="access_key родительской локации для иерархии."
    )

    # --- Категоризация ---
    specific_category: Mapped[str] = mapped_column(
        String(50),
        comment="Внутренний тип для логики: QUARTER, HUB_LOCATION, POI, INTERIOR, GATEWAY."
    )
    unified_display_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Внешний тип для отображения (для ботов и т.д.): Город, Магазин."
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True,
        comment='Теги для логики: ["безопасная_зона", "торговля"].'
    )

    # --- Контент и Презентация ---
    name: Mapped[str] = mapped_column(
        String(255), comment="Отображаемое название локации."
    )
    description: Mapped[Optional[str]] = mapped_column(
        TEXT, nullable=True, comment="Основной описательный текст для панорамы."
    )
    presentation: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True,
        comment='Данные для панорамы: {"image_url": "...", "sound_key": "..."}.'
    )
    flavor_text_options: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, comment="Список случайных фраз для разнообразия."
    )

    # --- Навигация и Логика ---
    exits: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSONB, nullable=True,
        comment='Список выходов: [{"label": "Войти", "target": "1-50-01-001"}].'
    )
    entry_point_location_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Для QUARTER: access_key точки входа в квартал."
    )
    skeleton_template_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="ID шаблона для процедурной генерации (если используется)."
    )

    # --- Служебные Поля ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text('now()')
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), server_default=text('now()')
    )

    # --- Отношения для удобной работы в коде ---
    parent_location: Mapped[Optional['GameLocation']] = relationship(
        'GameLocation', remote_side=[access_key], back_populates='child_locations'
    )
    child_locations: Mapped[List['GameLocation']] = relationship(
        'GameLocation', back_populates='parent_location'
    )

    def __repr__(self):
        return (f"<GameLocation(access_key='{self.access_key}', "
                f"name='{self.name}', category='{self.specific_category}')>")
