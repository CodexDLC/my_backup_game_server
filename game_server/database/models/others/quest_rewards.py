from ..models import Base

class QuestRewards(Base):
    __tablename__ = 'quest_rewards'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='quest_rewards_pkey'),
        UniqueConstraint('reward_key', name='quest_rewards_reward_key_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reward_key: Mapped[str] = mapped_column(String(100))
    reward_name: Mapped[str] = mapped_column(Text)
    reward_value: Mapped[int] = mapped_column(Integer)
    reward_type: Mapped[str] = mapped_column(Text)
    reward_description: Mapped[Optional[str]] = mapped_column(Text)

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_rewards')


