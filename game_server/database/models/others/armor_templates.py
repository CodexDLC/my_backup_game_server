from ..models import Base

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
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))


