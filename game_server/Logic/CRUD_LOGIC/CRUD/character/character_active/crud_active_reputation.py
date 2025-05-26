from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_reputation(action: str, reputation_id: int = None, reputation_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `reputation`."""
    
    if action == "insert" and reputation_data:
        query = text("""
            INSERT INTO reputation (reputation_id, character_id, faction_id, reputation_value, reputation_status)
            VALUES (:reputation_id, :character_id, :faction_id, :reputation_value, :reputation_status)
        """)
        await db_session.execute(query, {"reputation_id": reputation_id, **reputation_data})
        await db_session.commit()
        return {"status": "success", "message": f"Репутация `{reputation_data['reputation_status']}` добавлена персонажу `{reputation_data['character_id']}`"}

    elif action == "get" and reputation_id:
        query = text("SELECT * FROM reputation WHERE reputation_id = :reputation_id")
        result = await db_session.execute(query, {"reputation_id": reputation_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Репутация не найдена"}

    elif action == "update" and reputation_id and reputation_data:
        updates = ", ".join(f"{key} = :{key}" for key in reputation_data.keys())
        query = text(f"""
            UPDATE reputation SET {updates}
            WHERE reputation_id = :reputation_id
        """)
        await db_session.execute(query, {"reputation_id": reputation_id, **reputation_data})
        await db_session.commit()
        return {"status": "success", "message": f"Репутация `{reputation_id}` обновлена"}

    elif action == "delete" and reputation_id:
        query = text("DELETE FROM reputation WHERE reputation_id = :reputation_id")
        await db_session.execute(query, {"reputation_id": reputation_id})
        await db_session.commit()
        return {"status": "success", "message": f"Репутация `{reputation_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры"}
