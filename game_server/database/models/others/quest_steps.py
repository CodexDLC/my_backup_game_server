from ..models import Base

class QuestSteps(Base):
    __tablename__ = 'quest_steps'
    __table_args__ = (
        ForeignKeyConstraint(['quest_key'], ['quests.quest_key'], name='quest_steps_quest_key_fkey'),
        PrimaryKeyConstraint('step_key', name='quest_steps_pkey')
    )

    step_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    quest_key: Mapped[int] = mapped_column(Integer)
    step_order: Mapped[int] = mapped_column(Integer)
    description_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50))
    visibility_condition: Mapped[Optional[str]] = mapped_column(String(255))
    reward_key: Mapped[Optional[str]] = mapped_column(String(100))

    quests: Mapped['Quests'] = relationship('Quests', back_populates='quest_steps')
    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='quest_steps')


