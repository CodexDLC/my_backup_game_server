from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_materials(action: str, material_id: int = None, material_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `materials`."""
    
    if action == "insert" and material_data:
        query = text("""
            INSERT INTO materials (id, name, prefix, color, is_fragile, strength_percentage)
            VALUES (:id, :name, :prefix, :color, :is_fragile, :strength_percentage)
        """)
        await db_session.execute(query, {"id": material_id, **material_data})
        await db_session.commit()
        return {"status": "success", "message": f"Материал `{material_data['name']}` добавлен"}

    elif action == "get" and material_id:
        query = text("SELECT * FROM materials WHERE id = :material_id")
        result = await db_session.execute(query, {"material_id": material_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Материал не найден"}

    elif action == "update" and material_id and material_data:
        updates = ", ".join(f"{key} = :{key}" for key in material_data.keys())
        query = text(f"""
            UPDATE materials SET {updates}
            WHERE id = :material_id
        """)
        await db_session.execute(query, {"material_id": material_id, **material_data})
        await db_session.commit()
        return {"status": "success", "message": f"Материал `{material_id}` обновлён"}

    elif action == "delete" and material_id:
        query = text("DELETE FROM materials WHERE id = :material_id")
        await db_session.execute(query, {"material_id": material_id})
        await db_session.commit()
        return {"status": "success", "message": f"Материал `{material_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}
