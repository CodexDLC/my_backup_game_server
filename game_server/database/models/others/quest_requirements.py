from ..models import Base

class QuestRequirements(Base):
    __tablename__ = 'quest_requirements'
    __table_args__ = (
        PrimaryKeyConstraint('requirement_id', name='quest_requirements_pkey'),
        UniqueConstraint('requirement_key', name='quest_requirements_requirement_key_key')
    )

    requirement_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    requirement_key: Mapped[str] = mapped_column(String(100))
    requirement_name: Mapped[str] = mapped_column(String(255))
    requirement_value: Mapped[str] = mapped_column(String(255))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_requirements')


