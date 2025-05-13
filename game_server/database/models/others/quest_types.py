from ..models import Base

class QuestTypes(Base):
    __tablename__ = 'quest_types'
    __table_args__ = (
        PrimaryKeyConstraint('type_id', name='quest_types_pkey'),
        UniqueConstraint('type_key', name='quest_types_type_key_key')
    )

    type_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type_key: Mapped[str] = mapped_column(String(100))
    type_name: Mapped[str] = mapped_column(String(255))
    difficulty_level: Mapped[str] = mapped_column(String(50), server_default=text("'medium'::character varying"))

    quest_templates_master: Mapped[List['QuestTemplatesMaster']] = relationship('QuestTemplatesMaster', back_populates='quest_types')


