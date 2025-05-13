from ..models import Base

class Suffixes(Base):
    __tablename__ = 'suffixes'
    __table_args__ = (
        ForeignKeyConstraint(['mod1_code'], ['modifiers_library.access_modifier'], name='suffixes_mod1_code_fkey'),
        ForeignKeyConstraint(['mod2_code'], ['modifiers_library.access_modifier'], name='suffixes_mod2_code_fkey'),
        ForeignKeyConstraint(['mod3_code'], ['modifiers_library.access_modifier'], name='suffixes_mod3_code_fkey'),
        ForeignKeyConstraint(['mod4_code'], ['modifiers_library.access_modifier'], name='suffixes_mod4_code_fkey'),
        PrimaryKeyConstraint('suffix_code', name='suffixes_pkey')
    )

    suffix_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    fragment: Mapped[str] = mapped_column(Text)
    is_for_weapon: Mapped[bool] = mapped_column(Boolean)
    is_for_armor: Mapped[bool] = mapped_column(Boolean)
    is_for_accessory: Mapped[bool] = mapped_column(Boolean)
    mod1_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod1_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod2_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod2_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod3_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod3_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)
    mod4_code: Mapped[Optional[int]] = mapped_column(Integer)
    mod4_value: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric)

    modifiers_library: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod1_code], back_populates='suffixes')
    modifiers_library_: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod2_code], back_populates='suffixes_')
    modifiers_library1: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod3_code], back_populates='suffixes1')
    modifiers_library2: Mapped[Optional['ModifiersLibrary']] = relationship('ModifiersLibrary', foreign_keys=[mod4_code], back_populates='suffixes2')


