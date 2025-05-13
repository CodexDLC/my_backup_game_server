from ..models import Base

class Reputation(Base):
    __tablename__ = 'reputation'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='reputation_character_id_fkey'),
        PrimaryKeyConstraint('reputation_id', name='reputation_pkey')
    )

    reputation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reputation_value: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    reputation_status: Mapped[str] = mapped_column(String(50), server_default=text("'neutral'::character varying"))
    character_id: Mapped[Optional[int]] = mapped_column(Integer)
    faction_id: Mapped[Optional[int]] = mapped_column(Integer)

    character: Mapped[Optional['Characters']] = relationship('Characters', back_populates='reputation')


