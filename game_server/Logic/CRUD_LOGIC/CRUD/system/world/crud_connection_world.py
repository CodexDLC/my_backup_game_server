
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


async def manage_connection_types(action: str, type_id: str = None, type_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `connection_types`."""
    if action == "insert" and type_data:
        query = text("""
            INSERT INTO connection_types (id, name, description, time_cost)
            VALUES (:id, :name, :description, :time_cost)
        """)
        await db_session.execute(query, {"id": type_id, **type_data})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_data['name']}` добавлен"}

    elif action == "get" and type_id:
        query = text("SELECT * FROM connection_types WHERE id = :type_id")
        result = await db_session.execute(query, {"type_id": type_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Тип связи не найден"}

    elif action == "update" and type_id and type_data:
        updates = ", ".join(f"{key} = :{key}" for key in type_data.keys())
        query = text(f"""
            UPDATE connection_types SET {updates} WHERE id = :type_id
        """)
        await db_session.execute(query, {"type_id": type_id, **type_data})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_id}` обновлён"}

    elif action == "delete" and type_id:
        query = text("DELETE FROM connection_types WHERE id = :type_id")
        await db_session.execute(query, {"type_id": type_id})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_connections(action: str, connection_id: str = None, connection_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `connections`."""
    if action == "insert" and connection_data:
        query = text("""
            INSERT INTO connections (id, from_type, from_id, to_type, to_id, type_id, one_click, difficulty)
            VALUES (:id, :from_type, :from_id, :to_type, :to_id, :type_id, :one_click, :difficulty)
        """)
        await db_session.execute(query, {"id": connection_id, **connection_data})
        await db_session.commit()
        return {"status": "success", "message": f"Связь `{connection_data['from_type']} → {connection_data['to_type']}` добавлена"}

    elif action == "get" and connection_id:
        query = text("SELECT * FROM connections WHERE id = :connection_id")
        result = await db_session.execute(query, {"connection_id": connection_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Связь не найдена"}

    elif action == "update" and connection_id and connection_data:
        updates = ", ".join(f"{key} = :{key}" for key in connection_data.keys())
        query = text(f"""
            UPDATE connections SET {updates} WHERE id = :connection_id
        """)
        await db_session.execute(query, {"connection_id": connection_id, **connection_data})
        await db_session.commit()
        return {"status": "success", "message": f"Связь `{connection_id}` обновлена"}

    elif action == "delete" and connection_id:
        query = text("DELETE FROM connections WHERE id = :connection_id")
        await db_session.execute(query, {"connection_id": connection_id})
        await db_session.commit()
        return {"status": "success", "message": f"Связь `{connection_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры"}
