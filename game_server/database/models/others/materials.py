from ..models import Base

class Materials(Base):
    __tablename__ = 'materials'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='materials_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    prefix: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[Optional[str]] = mapped_column(Text)
    is_fragile: Mapped[Optional[bool]] = mapped_column(Boolean)
    strength_percentage: Mapped[Optional[int]] = mapped_column(Integer)


