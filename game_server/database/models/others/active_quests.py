from ..models import Base

class ActiveQuests(Base):
    __tablename__ = 'active_quests'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='active_quests_character_id_fkey'),
        PrimaryKeyConstraint('character_id', 'quest_id', name='active_quests_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(50), server_default=text("'active'::character varying"))
    current_step: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    quest_key: Mapped[Optional[str]] = mapped_column(String(100))
    flags_status: Mapped[Optional[dict]] = mapped_column(JSON)
    completion_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255))

    character: Mapped['Characters'] = relationship('Characters', back_populates='active_quests')


