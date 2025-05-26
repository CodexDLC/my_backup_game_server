


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_tick_summary(action: str, tick_id: int = None, tick_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `tick_summary`."""
    if action == "insert" and tick_data:
        query = text("""
            INSERT INTO tick_summary (character_id, hour_block, tick_count, mode, summary_data)
            VALUES (:character_id, :hour_block, :tick_count, :mode, :summary_data)
        """)
        await db_session.execute(query, tick_data)
        await db_session.commit()
        return {"status": "success", "message": f"Тик-данные для `{tick_data['character_id']}` добавлены"}

    elif action == "get" and tick_id:
        query = text("SELECT * FROM tick_summary WHERE id = :tick_id")
        result = await db_session.execute(query, {"tick_id": tick_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Тик-данные не найдены"}

    elif action == "update" and tick_id and tick_data:
        updates = ", ".join(f"{key} = :{key}" for key in tick_data.keys())
        query = text(f"""
            UPDATE tick_summary SET {updates} WHERE id = :tick_id
        """)
        await db_session.execute(query, {"tick_id": tick_id, **tick_data})
        await db_session.commit()
        return {"status": "success", "message": f"Тик-данные `{tick_id}` обновлены"}

    elif action == "delete" and tick_id:
        query = text("DELETE FROM tick_summary WHERE id = :tick_id")
        await db_session.execute(query, {"tick_id": tick_id})
        await db_session.commit()
        return {"status": "success", "message": f"Тик-данные `{tick_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_finish_handlers(action: str, batch_id: str = None, batch_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `finish_handlers`."""
    if action == "insert" and batch_data:
        query = text("""
            INSERT INTO finish_handlers (batch_id, task_type, completed_tasks, failed_tasks, status, error_message, timestamp, processed_by_coordinator)
            VALUES (:batch_id, :task_type, :completed_tasks, :failed_tasks, :status, :error_message, :timestamp, :processed_by_coordinator)
        """)
        await db_session.execute(query, {"batch_id": batch_id, **batch_data})
        await db_session.commit()
        return {"status": "success", "message": f"Обработчик `{batch_id}` добавлен"}

    elif action == "get" and batch_id:
        query = text("SELECT * FROM finish_handlers WHERE batch_id = :batch_id")
        result = await db_session.execute(query, {"batch_id": batch_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Обработчик не найден"}

    elif action == "update" and batch_id and batch_data:
        updates = ", ".join(f"{key} = :{key}" for key in batch_data.keys())
        query = text(f"""
            UPDATE finish_handlers SET {updates} WHERE batch_id = :batch_id
        """)
        await db_session.execute(query, {"batch_id": batch_id, **batch_data})
        await db_session.commit()
        return {"status": "success", "message": f"Обработчик `{batch_id}` обновлён"}

    elif action == "delete" and batch_id:
        query = text("DELETE FROM finish_handlers WHERE batch_id = :batch_id")
        await db_session.execute(query, {"batch_id": batch_id})
        await db_session.commit()
        return {"status": "success", "message": f"Обработчик `{batch_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}
