from ..models import Base

class QuestFlags(Base):
    __tablename__ = 'quest_flags'
    __table_args__ = (
        ForeignKeyConstraint(['flag_key_template'], ['flag_templates.flag_key'], ondelete='SET NULL', name='quest_flags_flag_key_template_fkey'),
        ForeignKeyConstraint(['quest_key'], ['quests.quest_key'], ondelete='CASCADE', name='quest_flags_quest_key_fkey'),
        ForeignKeyConstraint(['step_key'], ['quest_steps.step_key'], ondelete='CASCADE', name='quest_flags_step_key_fkey'),
        PrimaryKeyConstraint('flag_id', name='quest_flags_pkey'),
        UniqueConstraint('flag_key', name='quest_flags_flag_key_key')
    )

    flag_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    flag_key: Mapped[str] = mapped_column(String(100))
    value: Mapped[str] = mapped_column(Text)
    quest_key: Mapped[Optional[int]] = mapped_column(Integer)
    step_key: Mapped[Optional[str]] = mapped_column(String(100))
    flag_key_template: Mapped[Optional[str]] = mapped_column(String(100))

    flag_templates: Mapped[Optional['FlagTemplates']] = relationship('FlagTemplates', back_populates='quest_flags')
    quests: Mapped[Optional['Quests']] = relationship('Quests', back_populates='quest_flags')
    quest_steps: Mapped[Optional['QuestSteps']] = relationship('QuestSteps', back_populates='quest_flags')


