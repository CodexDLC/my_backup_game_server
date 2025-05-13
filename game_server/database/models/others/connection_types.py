from ..models import Base

class ConnectionTypes(Base):
    __tablename__ = 'connection_types'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='connection_types_pkey'),
        UniqueConstraint('name', name='connection_types_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String)
    time_cost: Mapped[int] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)

    connections: Mapped[List['Connections']] = relationship('Connections', back_populates='type')


