from ..models import Base

class QuestTemplatesMaster(Base):
    __tablename__ = 'quest_templates_master'
    __table_args__ = (
        ForeignKeyConstraint(['condition_key'], ['quest_conditions.condition_key'], name='quest_templates_master_condition_key_fkey'),
        ForeignKeyConstraint(['requirement_key'], ['quest_requirements.requirement_key'], name='quest_templates_master_requirement_key_fkey'),
        ForeignKeyConstraint(['reward_key'], ['quest_rewards.reward_key'], name='quest_templates_master_reward_key_fkey'),
        ForeignKeyConstraint(['type_key'], ['quest_types.type_key'], name='quest_templates_master_type_key_fkey'),
        PrimaryKeyConstraint('template_id', name='quest_templates_master_pkey'),
        UniqueConstraint('template_key', name='quest_templates_master_template_key_key')
    )

    template_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_key: Mapped[str] = mapped_column(String(100))
    type_key: Mapped[Optional[str]] = mapped_column(String(100))
    condition_key: Mapped[Optional[str]] = mapped_column(String(100))
    requirement_key: Mapped[Optional[str]] = mapped_column(String(100))
    reward_key: Mapped[Optional[str]] = mapped_column(String(100))

    quest_conditions: Mapped[Optional['QuestConditions']] = relationship('QuestConditions', back_populates='quest_templates_master')
    quest_requirements: Mapped[Optional['QuestRequirements']] = relationship('QuestRequirements', back_populates='quest_templates_master')
    quest_rewards: Mapped[Optional['QuestRewards']] = relationship('QuestRewards', back_populates='quest_templates_master')
    quest_types: Mapped[Optional['QuestTypes']] = relationship('QuestTypes', back_populates='quest_templates_master')


