from ..models import Base

class QuestConditions(Base):
    __tablename__ = 'quest_conditions'
    __table_args__ = (
        PrimaryKeyConstraint('condition_id', name='quest_conditions_pkey'),
        UniqueConstraint('condition_key', name='quest_conditions_condition_key_key')
    )

    condition_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    condition_key: Mapped[str] = mapped_column(String(100))
    condition_name: Mapped[str] = mapped_column(String(255))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_conditions')


