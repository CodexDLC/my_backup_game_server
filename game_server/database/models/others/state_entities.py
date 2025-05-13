from ..models import Base

class StateEntities(Base):
    __tablename__ = 'state_entities'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='state_entities_pkey'),
        UniqueConstraint('access_code', name='state_entities_access_code_key'),
        UniqueConstraint('code_name', name='state_entities_code_name_key'),
        Index('idx_state_entities_access_code', 'access_code'),
        Index('idx_state_entities_code_name', 'code_name'),
        Index('idx_state_entities_ui_type', 'ui_type')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer)
    code_name: Mapped[str] = mapped_column(Text)
    ui_type: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text, server_default=text("''::text"))
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('true'))


