from ..models import Base

class Connections(Base):
    __tablename__ = 'connections'
    __table_args__ = (
        CheckConstraint("from_type::text = ANY (ARRAY['region'::character varying, 'subregion'::character varying]::text[])", name='connections_from_type_check'),
        CheckConstraint("to_type::text = ANY (ARRAY['region'::character varying, 'subregion'::character varying]::text[])", name='connections_to_type_check'),
        ForeignKeyConstraint(['type_id'], ['connection_types.id'], name='connections_type_id_fkey'),
        PrimaryKeyConstraint('id', name='connections_pkey'),
        Index('idx_connections_from', 'from_type', 'from_id'),
        Index('idx_connections_to', 'to_type', 'to_id'),
        Index('idx_connections_type_id', 'type_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    from_type: Mapped[str] = mapped_column(String)
    from_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    to_type: Mapped[str] = mapped_column(String)
    to_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    type_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    one_click: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    difficulty: Mapped[int] = mapped_column(Integer, server_default=text('1'))

    type: Mapped['ConnectionTypes'] = relationship('ConnectionTypes', back_populates='connections')


