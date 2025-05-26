from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def manage_active_quests(action: str, character_id: int = None, quest_id: int = None, quest_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `active_quests`."""
    if action == "insert" and quest_data:
        query = text("""
            INSERT INTO active_quests (character_id, quest_id, quest_key, status, current_step, flags_status, completion_time, failure_reason)
            VALUES (:character_id, :quest_id, :quest_key, :status, :current_step, :flags_status, :completion_time, :failure_reason)
        """)
        await db_session.execute(query, {"character_id": character_id, "quest_id": quest_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_data['quest_key']}` добавлен для персонажа `{character_id}`"}

    elif action == "get" and character_id and quest_id:
        query = text("SELECT * FROM active_quests WHERE character_id = :character_id AND quest_id = :quest_id")
        result = await db_session.execute(query, {"character_id": character_id, "quest_id": quest_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Квест не найден"}

    elif action == "update" and character_id and quest_id and quest_data:
        updates = ", ".join(f"{key} = :{key}" for key in quest_data.keys())
        query = text(f"""
            UPDATE active_quests SET {updates} WHERE character_id = :character_id AND quest_id = :quest_id
        """)
        await db_session.execute(query, {"character_id": character_id, "quest_id": quest_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_id}` обновлён для `{character_id}`"}

    elif action == "delete" and character_id and quest_id:
        query = text("DELETE FROM active_quests WHERE character_id = :character_id AND quest_id = :quest_id")
        await db_session.execute(query, {"character_id": character_id, "quest_id": quest_id})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_id}` удалён для `{character_id}`"}

    return {"status": "error", "message": "Неверные параметры"}


