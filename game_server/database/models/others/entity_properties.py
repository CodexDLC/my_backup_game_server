from ..models import Base

class EntityProperties(Base):
    __tablename__ = 'entity_properties'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='entity_properties_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    key: Mapped[str] = mapped_column(String)
    value: Mapped[Optional[str]] = mapped_column(Text)


