from ..models import Base

class SpecialStatEffects(Base):
    __tablename__ = 'special_stat_effects'
    __table_args__ = (
        PrimaryKeyConstraint('stat_key', 'effect_field', name='special_stat_effects_pkey'),
    )

    stat_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    effect_field: Mapped[str] = mapped_column(String(50), primary_key=True)
    multiplier: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 4))
    description: Mapped[Optional[str]] = mapped_column(Text)


