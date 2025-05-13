from ..models import Base

class TemplateModifierDefaults(Base):
    __tablename__ = 'template_modifier_defaults'
    __table_args__ = (
        ForeignKeyConstraint(['access_modifier'], ['modifiers_library.access_modifier'], name='template_modifier_defaults_access_modifier_fkey'),
        ForeignKeyConstraint(['base_item_code'], ['item_base.base_item_code'], name='template_modifier_defaults_base_item_code_fkey'),
        PrimaryKeyConstraint('base_item_code', 'access_modifier', name='template_modifier_defaults_pkey')
    )

    base_item_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    access_modifier: Mapped[int] = mapped_column(Integer, primary_key=True)
    default_value: Mapped[decimal.Decimal] = mapped_column(Numeric)

    modifiers_library: Mapped['ModifiersLibrary'] = relationship('ModifiersLibrary', back_populates='template_modifier_defaults')
    item_base: Mapped['ItemBase'] = relationship('ItemBase', back_populates='template_modifier_defaults')


