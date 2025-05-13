from ..models import Base

class SkillUnlocks(Base):
    __tablename__ = 'skill_unlocks'
    __table_args__ = (
        ForeignKeyConstraint(['skill_key'], ['skills.skill_key'], ondelete='CASCADE', name='skill_unlocks_skill_key_fkey'),
        PrimaryKeyConstraint('skill_key', 'rank', name='skill_unlocks_pkey')
    )

    skill_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    rank: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    xp_threshold: Mapped[int] = mapped_column(BigInteger)
    rank_name: Mapped[str] = mapped_column(String(100))

    skills: Mapped['Skills'] = relationship('Skills', back_populates='skill_unlocks')


