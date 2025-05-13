from ..models import Base

class Worlds(Base):
    __tablename__ = 'worlds'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='worlds_pkey'),
        UniqueConstraint('name', name='worlds_name_key')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    name: Mapped[str] = mapped_column(String)
    is_static: Mapped[bool] = mapped_column(Boolean, server_default=text('true'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), server_default=text('now()'))

    discord_bindings: Mapped[List['DiscordBindings']] = relationship('DiscordBindings', back_populates='world')
    regions: Mapped[List['Regions']] = relationship('Regions', back_populates='world')
    state_entities_discord: Mapped[List['StateEntitiesDiscord']] = relationship('StateEntitiesDiscord', back_populates='world')


