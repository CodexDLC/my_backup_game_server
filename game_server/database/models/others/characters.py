from ..models import Base

class Characters(Base):
    __tablename__ = 'characters'
    __table_args__ = (
        ForeignKeyConstraint(['account_id'], ['account_info.account_id'], ondelete='CASCADE', name='characters_account_id_fkey'),
        ForeignKeyConstraint(['bloodline_id'], ['bloodlines.bloodline_id'], ondelete='SET NULL', name='characters_bloodline_id_fkey'),
        ForeignKeyConstraint(['race_id'], ['races.race_id'], ondelete='SET DEFAULT', onupdate='CASCADE', name='characters_race_id_fkey'),
        PrimaryKeyConstraint('character_id', name='characters_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    race_id: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    is_deleted: Mapped[bool] = mapped_column(Boolean, server_default=text('false'))
    account_id: Mapped[Optional[int]] = mapped_column(Integer)
    surname: Mapped[Optional[str]] = mapped_column(String(100))
    bloodline_id: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))

    account: Mapped[Optional['AccountInfo']] = relationship('AccountInfo', back_populates='characters')
    bloodline: Mapped[Optional['Bloodlines']] = relationship('Bloodlines', back_populates='characters')
    race: Mapped['Races'] = relationship('Races', back_populates='characters')
    active_quests: Mapped[List['ActiveQuests']] = relationship('ActiveQuests', back_populates='character')
    character_skills: Mapped[List['CharacterSkills']] = relationship('CharacterSkills', back_populates='character')
    inventory: Mapped[List['Inventory']] = relationship('Inventory', back_populates='character')
    progression_ticks: Mapped[List['ProgressionTicks']] = relationship('ProgressionTicks', back_populates='character')
    reputation: Mapped[List['Reputation']] = relationship('Reputation', back_populates='character')
    equipped_items: Mapped[List['EquippedItems']] = relationship('EquippedItems', back_populates='character')


