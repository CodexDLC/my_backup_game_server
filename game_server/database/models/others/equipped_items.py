from ..models import Base

class EquippedItems(Base):
    __tablename__ = 'equipped_items'
    __table_args__ = (
        ForeignKeyConstraint(['character_id'], ['characters.character_id'], ondelete='CASCADE', name='equipped_items_character_id_fkey'),
        ForeignKeyConstraint(['inventory_id'], ['inventory.inventory_id'], ondelete='CASCADE', name='equipped_items_inventory_id_fkey'),
        PrimaryKeyConstraint('character_id', 'inventory_id', name='equipped_items_pkey')
    )

    character_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    durability: Mapped[int] = mapped_column(Integer, server_default=text('100'))
    slot: Mapped[Optional[str]] = mapped_column(String(50))
    enchantment_effect: Mapped[Optional[dict]] = mapped_column(JSON)

    character: Mapped['Characters'] = relationship('Characters', back_populates='equipped_items')
    inventory: Mapped['Inventory'] = relationship('Inventory', back_populates='equipped_items')
