from ..models import Base

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


