from ..models import Base

class Inventory(Base):
    __tablename__ = 'inventory'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='inventory_character_id_fkey'),
        PrimaryKeyConstraint('inventory_id', name='inventory_pkey'),
        Index('idx_inventory_character', 'character_id')
    )

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    item_id: Mapped[Optional[int]] = mapped_column(Integer)
    acquired_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    character: Mapped['Characters'] = relationship('Characters', back_populates='inventory')
    equipped_items: Mapped[List['EquippedItems']] = relationship('EquippedItems', back_populates='inventory')


class PlayerMagicAttack(Characters):
    __tablename__ = 'player_magic_attack'
    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['characters.character_id'], ondelete='CASCADE', name='player_magic_attack_player_id_fkey'),
        PrimaryKeyConstraint('player_id', name='player_magic_attack_pkey')
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


class PlayerMagicDefense(Characters):
    __tablename__ = 'player_magic_defense'
    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['characters.character_id'], ondelete='CASCADE', name='player_magic_defense_player_id_fkey'),
        PrimaryKeyConstraint('player_id', name='player_magic_defense_pkey')
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


class PlayerPhysicalAttack(Characters):
    __tablename__ = 'player_physical_attack'
    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['characters.character_id'], ondelete='CASCADE', name='player_physical_attack_player_id_fkey'),
        PrimaryKeyConstraint('player_id', name='player_physical_attack_pkey')
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))


class PlayerPhysicalDefense(Characters):
    __tablename__ = 'player_physical_defense'
    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['characters.character_id'], ondelete='CASCADE', name='player_physical_defense_player_id_fkey'),
        PrimaryKeyConstraint('player_id', name='player_physical_defense_pkey')
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    piercing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    slashing_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    blunt_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    cutting_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    physical_resistance_percent: Mapped[Optional[float]] = mapped_column(Double(53))


