from ..models import Base

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


