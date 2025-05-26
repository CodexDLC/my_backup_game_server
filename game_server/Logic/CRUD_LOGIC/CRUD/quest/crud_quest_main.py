
from sqlalchemy import text
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession


async def manage_quests(action: str, quest_id: int = None, quest_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quests`."""
    if action == "insert" and quest_data:
        query = text("""
            INSERT INTO quests (quest_id, quest_key, quest_name, description_key, reward_key, progress_flag, status)
            VALUES (:quest_id, :quest_key, :quest_name, :description_key, :reward_key, :progress_flag, :status)
        """)
        await db_session.execute(query, {"quest_id": quest_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_data['quest_name']}` добавлен"}

    elif action == "get" and quest_id:
        query = text("SELECT * FROM quests WHERE quest_id = :quest_id")
        result = await db_session.execute(query, {"quest_id": quest_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Квест не найден"}

    elif action == "update" and quest_id and quest_data:
        updates = ", ".join(f"{key} = :{key}" for key in quest_data.keys())
        query = text(f"""
            UPDATE quests SET {updates} WHERE quest_id = :quest_id
        """)
        await db_session.execute(query, {"quest_id": quest_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_id}` обновлён"}

    elif action == "delete" and quest_id:
        query = text("DELETE FROM quests WHERE quest_id = :quest_id")
        await db_session.execute(query, {"quest_id": quest_id})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{quest_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_steps(action: str, step_key: str = None, step_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_steps`."""
    if action == "insert" and step_data:
        query = text("""
            INSERT INTO quest_steps (step_key, quest_key, step_order, description_key, visibility_condition, reward_key, status)
            VALUES (:step_key, :quest_key, :step_order, :description_key, :visibility_condition, :reward_key, :status)
        """)
        await db_session.execute(query, {"step_key": step_key, **step_data})
        await db_session.commit()
        return {"status": "success", "message": f"Шаг `{step_key}` добавлен"}

    elif action == "get" and step_key:
        query = text("SELECT * FROM quest_steps WHERE step_key = :step_key")
        result = await db_session.execute(query, {"step_key": step_key})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Шаг не найден"}

    elif action == "update" and step_key and step_data:
        updates = ", ".join(f"{key} = :{key}" for key in step_data.keys())
        query = text(f"""
            UPDATE quest_steps SET {updates} WHERE step_key = :step_key
        """)
        await db_session.execute(query, {"step_key": step_key, **step_data})
        await db_session.commit()
        return {"status": "success", "message": f"Шаг `{step_key}` обновлён"}

    elif action == "delete" and step_key:
        query = text("DELETE FROM quest_steps WHERE step_key = :step_key")
        await db_session.execute(query, {"step_key": step_key})
        await db_session.commit()
        return {"status": "success", "message": f"Шаг `{step_key}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_flags(action: str, flag_id: int = None, flag_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_flags`."""
    if action == "insert" and flag_data:
        query = text("""
            INSERT INTO quest_flags (flag_id, flag_key, quest_key, step_key, flag_key_template, value)
            VALUES (:flag_id, :flag_key, :quest_key, :step_key, :flag_key_template, :value)
        """)
        await db_session.execute(query, {"flag_id": flag_id, **flag_data})
        await db_session.commit()
        return {"status": "success", "message": f"Флаг `{flag_data['flag_key']}` добавлен"}

    elif action == "get" and flag_id:
        query = text("SELECT * FROM quest_flags WHERE flag_id = :flag_id")
        result = await db_session.execute(query, {"flag_id": flag_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Флаг не найден"}

    elif action == "update" and flag_id and flag_data:
        updates = ", ".join(f"{key} = :{key}" for key in flag_data.keys())
        query = text(f"""
            UPDATE quest_flags SET {updates} WHERE flag_id = :flag_id
        """)
        await db_session.execute(query, {"flag_id": flag_id, **flag_data})
        await db_session.commit()
        return {"status": "success", "message": f"Флаг `{flag_id}` обновлён"}

    elif action == "delete" and flag_id:
        query = text("DELETE FROM quest_flags WHERE flag_id = :flag_id")
        await db_session.execute(query, {"flag_id": flag_id})
        await db_session.commit()
        return {"status": "success", "message": f"Флаг `{flag_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


