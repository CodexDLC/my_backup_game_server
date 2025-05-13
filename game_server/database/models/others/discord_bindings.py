from ..models import Base

class DiscordBindings(Base):
    __tablename__ = 'discord_bindings'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='discord_bindings_world_id_fkey'),
        PrimaryKeyConstraint('guild_id', 'entity_access_key', name='discord_bindings_pkey'),
        Index('idx_discord_bindings_channel', 'channel_id')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    permissions: Mapped[int] = mapped_column(Integer, server_default=text('0'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))
    category_id: Mapped[Optional[str]] = mapped_column(String)
    channel_id: Mapped[Optional[str]] = mapped_column(String)

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='discord_bindings')
    applied_permissions: Mapped[List['AppliedPermissions']] = relationship('AppliedPermissions', back_populates='discord_bindings')


