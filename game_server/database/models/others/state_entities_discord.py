from ..models import Base

class StateEntitiesDiscord(Base):
    __tablename__ = 'state_entities_discord'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='state_entities_discord_world_id_fkey'),
        PrimaryKeyConstraint('guild_id', 'access_code', name='state_entities_discord_pkey'),
        Index('idx_state_entities_discord_role_id', 'role_id'),
        Index('idx_state_entities_discord_updated_at', 'updated_at')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(Text)
    role_id: Mapped[int] = mapped_column(BigInteger)
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='state_entities_discord')


