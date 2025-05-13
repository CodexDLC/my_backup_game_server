from ..models import Base

class AppliedPermissions(Base):
    __tablename__ = 'applied_permissions'
    __table_args__ = (
        ForeignKeyConstraint(['guild_id', 'entity_access_key'], ['discord_bindings.guild_id', 'discord_bindings.entity_access_key'], ondelete='CASCADE', name='applied_permissions_guild_id_entity_access_key_fkey'),
        PrimaryKeyConstraint('guild_id', 'entity_access_key', 'access_code', 'target_type', 'target_id', 'role_id', name='applied_permissions_pkey'),
        Index('idx_applied_on_date', 'applied_at'),
        Index('idx_applied_on_role', 'guild_id', 'role_id'),
        Index('idx_applied_on_target', 'guild_id', 'target_type', 'target_id')
    )

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_type: Mapped[str] = mapped_column(Text, primary_key=True)
    target_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    role_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    applied_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    discord_bindings: Mapped['DiscordBindings'] = relationship('DiscordBindings', back_populates='applied_permissions')


