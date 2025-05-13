from ..models import Base

class Subregions(Base):
    __tablename__ = 'subregions'
    __table_args__ = (
        ForeignKeyConstraint(['region_id'], ['regions.id'], ondelete='CASCADE', name='subregions_region_id_fkey'),
        PrimaryKeyConstraint('id', name='subregions_pkey'),
        UniqueConstraint('access_key', name='subregions_access_key_key'),
        Index('idx_subregions_access_key', 'access_key'),
        Index('idx_subregions_name', 'name'),
        Index('idx_subregions_peaceful', 'is_peaceful'),
        Index('idx_subregions_region_id', 'region_id')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    region_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    access_key: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    is_peaceful: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    description: Mapped[Optional[str]] = mapped_column(Text)

    region: Mapped['Regions'] = relationship('Regions', back_populates='subregions')


