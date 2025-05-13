from ..models import Base

class FlagTemplates(Base):
    __tablename__ = 'flag_templates'
    __table_args__ = (
        PrimaryKeyConstraint('flag_key', name='flag_templates_pkey'),
    )

    flag_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    flag_category: Mapped[str] = mapped_column(String(50))
    flag_description: Mapped[str] = mapped_column(String(255))

    quest_flags: Mapped[List['QuestFlags']] = relationship('QuestFlags', back_populates='flag_templates')


