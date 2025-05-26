from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_equipped_items(action: str, character_id: int = None, equipped_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `equipped_items`."""
    
    if action == "insert" and equipped_data:
        query = text("""
            INSERT INTO equipped_items (character_id, inventory_id, slot, durability, enchantment_effect)
            VALUES (:character_id, :inventory_id, :slot, :durability, :enchantment_effect)
        """)
        await db_session.execute(query, {"character_id": character_id, **equipped_data})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{equipped_data['slot']}` экипирован персонажу `{character_id}`"}

    elif action == "get" and character_id:
        query = text("SELECT * FROM equipped_items WHERE character_id = :character_id")
        result = await db_session.execute(query, {"character_id": character_id})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Предметы не найдены"}

    elif action == "update" and character_id and equipped_data:
        updates = ", ".join(f"{key} = :{key}" for key in equipped_data.keys())
        query = text(f"""
            UPDATE equipped_items SET {updates}
            WHERE character_id = :character_id
        """)
        await db_session.execute(query, {"character_id": character_id, **equipped_data})
        await db_session.commit()
        return {"status": "success", "message": f"Экипировка `{character_id}` обновлена"}

    elif action == "delete" and character_id:
        query = text("DELETE FROM equipped_items WHERE character_id = :character_id")
        await db_session.execute(query, {"character_id": character_id})
        await db_session.commit()
        return {"status": "success", "message": f"Экипировка `{character_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_inventory(action: str, inventory_id: int = None, inventory_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `inventory`."""
    
    if action == "insert" and inventory_data:
        query = text("""
            INSERT INTO inventory (inventory_id, character_id, item_id, quantity, acquired_at)
            VALUES (:inventory_id, :character_id, :item_id, :quantity, CURRENT_TIMESTAMP)
        """)
        await db_session.execute(query, {"inventory_id": inventory_id, **inventory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{inventory_data['item_id']}` добавлен в инвентарь персонажа `{inventory_data['character_id']}`"}

    elif action == "get" and inventory_id:
        query = text("SELECT * FROM inventory WHERE inventory_id = :inventory_id")
        result = await db_session.execute(query, {"inventory_id": inventory_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Предмет в инвентаре не найден"}

    elif action == "update" and inventory_id and inventory_data:
        updates = ", ".join(f"{key} = :{key}" for key in inventory_data.keys())
        query = text(f"""
            UPDATE inventory SET {updates}
            WHERE inventory_id = :inventory_id
        """)
        await db_session.execute(query, {"inventory_id": inventory_id, **inventory_data})
        await db_session.commit()
        return {"status": "success", "message": f"Инвентарь `{inventory_id}` обновлён"}

    elif action == "delete" and inventory_id:
        query = text("DELETE FROM inventory WHERE inventory_id = :inventory_id")
        await db_session.execute(query, {"inventory_id": inventory_id})
        await db_session.commit()
        return {"status": "success", "message": f"Предмет `{inventory_id}` удалён из инвентаря"}

    return {"status": "error", "message": "Неверные параметры"}

