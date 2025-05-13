from ..models import Base

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


