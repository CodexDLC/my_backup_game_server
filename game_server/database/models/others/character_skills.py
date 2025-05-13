from ..models import Base

class CharacterSkills(Base):
    __tablename__ = 'character_skills'
    __table_args__ = (
        CheckConstraint("progress_state::text = ANY (ARRAY['PLUS'::character varying, 'PAUSE'::character varying, 'MINUS'::character varying]::text[])", name='character_skills_progress_state_check'),
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='character_skills_character_id_fkey'),
        ForeignKeyConstraint(['skill_id'], ['skills.skill_id'], ondelete='CASCADE', name='character_skills_skill_id_fkey'),
        PrimaryKeyConstraint('character_id', 'skill_id', name='character_skills_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[int] = mapped_column(Integer, server_default=text('1'))
    xp: Mapped[int] = mapped_column(BigInteger, server_default=text('0'))
    progress_state: Mapped[str] = mapped_column(String(10), server_default=text("'PLUS'::character varying"))

    character: Mapped['Characters'] = relationship('Characters', back_populates='character_skills')
    skill: Mapped['Skills'] = relationship('Skills', back_populates='character_skills')


class CharacterStatus(Characters):
    __tablename__ = 'character_status'
    __table_args__ = (
        ForeignKeyConstraint(['player_id'], ['characters.character_id'], ondelete='CASCADE', name='character_status_player_id_fkey'),
        PrimaryKeyConstraint('player_id', name='character_status_pkey')
    )

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    current_health: Mapped[Optional[int]] = mapped_column(Integer)
    max_health: Mapped[Optional[int]] = mapped_column(Integer)
    experience: Mapped[Optional[int]] = mapped_column(Integer)
    level: Mapped[Optional[int]] = mapped_column(Integer)
    current_energy: Mapped[Optional[int]] = mapped_column(Integer)
    crit_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    crit_damage_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_crit_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_crit_damage: Mapped[Optional[float]] = mapped_column(Double(53))
    dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    anti_dodge_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    counter_attack_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    parry_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    block_chance: Mapped[Optional[float]] = mapped_column(Double(53))
    armor_penetration: Mapped[Optional[float]] = mapped_column(Double(53))
    physical_attack: Mapped[Optional[float]] = mapped_column(Double(53))
    magical_attack: Mapped[Optional[float]] = mapped_column(Double(53))
    magic_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    physical_resistance: Mapped[Optional[float]] = mapped_column(Double(53))
    mana_cost_reduction: Mapped[Optional[float]] = mapped_column(Double(53))
    regen_health_rate: Mapped[Optional[float]] = mapped_column(Double(53))
    energy_regeneration_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    energy_pool_bonus: Mapped[Optional[int]] = mapped_column(Integer)
    absorption_bonus: Mapped[Optional[float]] = mapped_column(Double(53))
    shield_value: Mapped[Optional[float]] = mapped_column(Double(53))
    shield_regeneration: Mapped[Optional[float]] = mapped_column(Double(53))
    gear_score: Mapped[Optional[int]] = mapped_column(Integer)
    luck: Mapped[Optional[float]] = mapped_column(Double(53))
    created_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, server_default=text('CURRENT_TIMESTAMP'))
    IE: Mapped[Optional[int]] = mapped_column(Integer)


class CharactersSpecial(Characters):
    __tablename__ = 'characters_special'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='characters_special_character_id_fkey'),
        PrimaryKeyConstraint('character_id', name='characters_special_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    strength: Mapped[Optional[int]] = mapped_column(Integer)
    perception: Mapped[Optional[int]] = mapped_column(Integer)
    endurance: Mapped[Optional[int]] = mapped_column(Integer)
    agility: Mapped[Optional[int]] = mapped_column(Integer)
    intelligence: Mapped[Optional[int]] = mapped_column(Integer)
    charisma: Mapped[Optional[int]] = mapped_column(Integer)
    luck: Mapped[Optional[int]] = mapped_column(Integer)


