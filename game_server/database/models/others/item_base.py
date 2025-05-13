from ..models import Base

class ItemBase(Base):
    __tablename__ = 'item_base'
    __table_args__ = (
        PrimaryKeyConstraint('base_item_code', name='item_base_pkey'),
    )

    base_item_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(Text)
    equip_slot: Mapped[str] = mapped_column(Text)
    base_durability: Mapped[int] = mapped_column(Integer)
    base_weight: Mapped[int] = mapped_column(Integer)

    template_modifier_defaults: Mapped[List['TemplateModifierDefaults']] = relationship('TemplateModifierDefaults', back_populates='item_base')


