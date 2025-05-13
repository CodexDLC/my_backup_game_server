from ..models import Base

class ProgressionTicks(Base):
    __tablename__ = 'progression_ticks'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='progression_ticks_character_id_fkey'),
        ForeignKeyConstraint(['skill_id'], ['skills.skill_id'], ondelete='CASCADE', name='progression_ticks_skill_id_fkey'),
        PrimaryKeyConstraint('tick_id', name='progression_ticks_pkey')
    )

    tick_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[Optional[int]] = mapped_column(Integer)
    skill_id: Mapped[Optional[int]] = mapped_column(Integer)
    xp_generated: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    character: Mapped[Optional['Characters']] = relationship('Characters', back_populates='progression_ticks')
    skill: Mapped[Optional['Skills']] = relationship('Skills', back_populates='progression_ticks')


