from ..models import Base

class Bloodlines(Base):
    __tablename__ = 'bloodlines'
    __table_args__ = (
        PrimaryKeyConstraint('bloodline_id', name='bloodlines_pkey'),
    )

    bloodline_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bloodline_name: Mapped[str] = mapped_column(String(100), server_default=text("'human'::character varying"))

    characters: Mapped[List['Characters']] = relationship('Characters', back_populates='bloodline')


