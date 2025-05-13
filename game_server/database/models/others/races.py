from ..models import Base

class Races(Base):
    __tablename__ = 'races'
    __table_args__ = (
        PrimaryKeyConstraint('race_id', name='races_pkey'),
    )

    race_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), server_default=text("''::character varying"))
    founder_id: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    characters: Mapped[List['Characters']] = relationship('Characters', back_populates='race')


