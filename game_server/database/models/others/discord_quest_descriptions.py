from ..models import Base

class DiscordQuestDescriptions(Base):
    __tablename__ = 'discord_quest_descriptions'
    __table_args__ = (
        PrimaryKeyConstraint('description_key', name='discord_quest_descriptions_pkey'),
    )

    description_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    text_: Mapped[str] = mapped_column('text', Text)


