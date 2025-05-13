from ..models import Base

class Quests(Base):
    __tablename__ = 'quests'
    __table_args__ = (
        PrimaryKeyConstraint('quest_id', name='quests_pkey'),
        UniqueConstraint('description_key', name='quests_description_key_key'),
        UniqueConstraint('quest_key', name='quests_quest_key_key'),
        UniqueConstraint('reward_key', name='quests_reward_key_key')
    )

    quest_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quest_key: Mapped[int] = mapped_column(Integer)
    quest_name: Mapped[str] = mapped_column(String(255))
    description_key: Mapped[str] = mapped_column(String(100))
    reward_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), server_default=text("'inactive'::character varying"))
    progress_flag: Mapped[Optional[str]] = mapped_column(String(255), server_default=text('NULL::character varying'))

    quest_steps: Mapped[List['QuestSteps']] = relationship('QuestSteps', back_populates='quests')
    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='quests')


