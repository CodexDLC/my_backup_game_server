from ..models import Base

class ModifiersLibrary(Base):
    __tablename__ = 'modifiers_library'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='modifiers_library_pkey'),
        UniqueConstraint('access_modifier', name='modifiers_library_access_modifier_key'),
        UniqueConstraint('modifier_name', name='modifiers_library_modifier_name_key')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_modifier: Mapped[int] = mapped_column(Integer)
    modifier_name: Mapped[str] = mapped_column(Text)
    effect_description: Mapped[Optional[str]] = mapped_column(Text)

    suffixes: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod1_code]', back_populates='modifiers_library')
    suffixes_: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod2_code]', back_populates='modifiers_library_')
    suffixes1: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod3_code]', back_populates='modifiers_library1')
    suffixes2: Mapped[List['Suffixes']] = relationship('Suffixes', foreign_keys='[Suffixes.mod4_code]', back_populates='modifiers_library2')
    template_modifier_defaults: Mapped[List['TemplateModifierDefaults']] = relationship('TemplateModifierDefaults', back_populates='modifiers_library')


