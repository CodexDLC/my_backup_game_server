import enum
import uuid

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Boolean,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Text,
    text
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from typing import List

# --- Базовая настройка SQLAlchemy ---
Base = declarative_base()


# --- Определение Enum для location_type ---
class LocationTypeEnum(enum.Enum):
    open = 'open'
    transition = 'transition'
    internal = 'internal'


# --- Модели данных (Таблицы) ---

class GameLocation(Base):
    """
    Модель для таблицы game_locations.
    Хранит информацию о локациях-контейнерах, таких как города, кварталы, здания.
    """
    __tablename__ = 'game_locations'

    # Основные идентификаторы
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')
    )
    access_key: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)

    # Описательная информация (ключи для локализации)
    display_name_key: Mapped[str] = mapped_column(String, nullable=False)
    description_key: Mapped[str] = mapped_column(Text, nullable=True)

    # Классификация и свойства
    location_type: Mapped[LocationTypeEnum] = mapped_column(
        SQLAlchemyEnum(LocationTypeEnum, name='location_type_enum'), nullable=False
    )
    tags: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)

    # Ключи для ресурсов клиента
    background_art_key: Mapped[str] = mapped_column(String, nullable=True)
    ambient_sound_key: Mapped[str] = mapped_column(String, nullable=True)
    
    # Скриптинг
    on_enter_event_script: Mapped[str] = mapped_column(String, nullable=True)

    # Связь с точкой входа (NavigationNode)
    entry_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('navigation_nodes.node_id'), nullable=False
    )
    entry_node: Mapped['NavigationNode'] = relationship(foreign_keys=[entry_node_id])

    # Отношение "один ко многим": одна локация может иметь много узлов навигации
    nodes: Mapped[List['NavigationNode']] = relationship(
        back_populates='location',
        foreign_keys='NavigationNode.location_id',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<GameLocation(access_key='{self.access_key}', name_key='{self.display_name_key}')>"


class NavigationNode(Base):
    """
    Модель для таблицы navigation_nodes.
    Хранит информацию о конкретных точках интереса внутри локации.
    """
    __tablename__ = 'navigation_nodes'

    node_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')
    )
    
    # Внешний ключ к родительской локации
    location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey('game_locations.location_id'), nullable=False
    )

    # Описательная информация
    display_name_key: Mapped[str] = mapped_column(String, nullable=True)
    
    # Визуальные параметры
    coordinates: Mapped[str] = mapped_column(String, nullable=False) # Например, "{'x': 120, 'y': 340}"
    camera_angle_id: Mapped[int] = mapped_column(Integer, nullable=True)

    # Отношение "многие к одному": много узлов принадлежат одной локации
    location: Mapped['GameLocation'] = relationship(
        back_populates='nodes', foreign_keys=[location_id]
    )

    # --- ИСПРАВЛЕННЫЙ СИНТАКСИС ---
    # Отношения для переходов
    outgoing_edges: Mapped[List['TransitionEdge']] = relationship(
        back_populates='from_node',
        foreign_keys='TransitionEdge.from_node_id',
        cascade="all, delete-orphan"
    )
    incoming_edges: Mapped[List['TransitionEdge']] = relationship(
        back_populates='to_node',
        foreign_keys='TransitionEdge.to_node_id',
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<NavigationNode(id='{self.node_id}', name_key='{self.display_name_key}')>"


class TransitionEdge(Base):
    """
    Модель для таблицы transition_edges.
    Описывает правила и условия перемещения между двумя узлами (NavigationNode).
    """
    __tablename__ = 'transition_edges'

    edge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()')
    )
    
    # Связь с начальным и конечным узлами
    from_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('navigation_nodes.node_id'), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey('navigation_nodes.node_id'), nullable=False)

    # UI и анимации
    ui_button_label_key: Mapped[str] = mapped_column(String, nullable=False)
    transition_animation_key: Mapped[str] = mapped_column(String, nullable=True)

    # Логика и условия доступа
    is_enabled_by_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    required_item_id: Mapped[str] = mapped_column(String, nullable=True)
    required_world_state_flags: Mapped[dict] = mapped_column(JSONB, nullable=True)

    # Скриптинг
    on_traverse_event_script: Mapped[str] = mapped_column(String, nullable=True)

    # Отношения "многие к одному" для начального и конечного узлов
    from_node: Mapped['NavigationNode'] = relationship(
        back_populates='outgoing_edges', foreign_keys=[from_node_id]
    )
    to_node: Mapped['NavigationNode'] = relationship(
        back_populates='incoming_edges', foreign_keys=[to_node_id]
    )

    def __repr__(self):
        return f"<TransitionEdge(from='{self.from_node_id}', to='{self.to_node_id}')>"

