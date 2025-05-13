from ..models import Base

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


