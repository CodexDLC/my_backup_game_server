from ..models import Base

class Regions(Base):
    __tablename__ = 'regions'
    __table_args__ = (
        ForeignKeyConstraint(['world_id'], ['worlds.id'], ondelete='CASCADE', name='regions_world_id_fkey'),
        PrimaryKeyConstraint('id', name='regions_pkey'),
        UniqueConstraint('access_key', name='regions_access_key_key'),
        Index('idx_regions_access_key', 'access_key'),
        Index('idx_regions_name', 'name'),
        Index('idx_regions_world_id', 'world_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    world_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_key: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(Text)

    world: Mapped['Worlds'] = relationship('Worlds', back_populates='regions')
    subregions: Mapped[List['Subregions']] = relationship('Subregions', back_populates='region')


