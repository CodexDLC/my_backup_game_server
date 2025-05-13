from ..models import Base

class EntityStateMap(Base):
    __tablename__ = 'entity_state_map'
    __table_args__ = (
        PrimaryKeyConstraint('entity_access_key', 'access_code', name='entity_state_map_pkey'),
        Index('idx_esm_access_code', 'access_code')
    )

    entity_access_key: Mapped[str] = mapped_column(String, primary_key=True)
    access_code: Mapped[int] = mapped_column(Integer, primary_key=True)


