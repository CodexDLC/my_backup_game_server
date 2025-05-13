from ..models import Base

class Skills(Base):
    __tablename__ = 'skills'
    __table_args__ = (
        PrimaryKeyConstraint('skill_id', name='skills_pkey'),
        UniqueConstraint('skill_key', name='skills_skill_key_key')
    )

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_key: Mapped[str] = mapped_column(String(100))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    skill_group: Mapped[Optional[str]] = mapped_column(String(50))
    main_special: Mapped[Optional[str]] = mapped_column(String(50))
    secondary_special: Mapped[Optional[str]] = mapped_column(String(50))

    skill_ability_unlocks: Mapped[List['SkillAbilityUnlocks']] = relationship('SkillAbilityUnlocks', back_populates='skills')
    skill_unlocks: Mapped[List['SkillUnlocks']] = relationship('SkillUnlocks', back_populates='skills')
    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='skill')
    progression_ticks: Mapped[List['ProgressionTicks']] = relationship('ProgressionTicks', back_populates='skill')


