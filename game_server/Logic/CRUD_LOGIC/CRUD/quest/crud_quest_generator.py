

from sqlalchemy import text
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession

async def manage_quest_templates_master(action: str, template_id: int = None, quest_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_templates_master`."""
    if action == "insert" and quest_data:
        query = text("""
            INSERT INTO quest_templates_master (template_id, template_key, type_key, condition_key, requirement_key, reward_key)
            VALUES (:template_id, :template_key, :type_key, :condition_key, :requirement_key, :reward_key)
        """)
        await db_session.execute(query, {"template_id": template_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Шаблон `{quest_data['template_key']}` добавлен"}

    elif action == "get" and template_id:
        query = text("SELECT * FROM quest_templates_master WHERE template_id = :template_id")
        result = await db_session.execute(query, {"template_id": template_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Шаблон не найден"}

    elif action == "update" and template_id and quest_data:
        updates = ", ".join(f"{key} = :{key}" for key in quest_data.keys())
        query = text(f"""
            UPDATE quest_templates_master SET {updates} WHERE template_id = :template_id
        """)
        await db_session.execute(query, {"template_id": template_id, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Шаблон `{template_id}` обновлён"}

    elif action == "delete" and template_id:
        query = text("DELETE FROM quest_templates_master WHERE template_id = :template_id")
        await db_session.execute(query, {"template_id": template_id})
        await db_session.commit()
        return {"status": "success", "message": f"Шаблон `{template_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_types(action: str, type_id: int = None, type_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_types`."""
    if action == "insert" and type_data:
        query = text("""
            INSERT INTO quest_types (type_id, type_key, type_name, difficulty_level)
            VALUES (:type_id, :type_key, :type_name, :difficulty_level)
        """)
        await db_session.execute(query, {"type_id": type_id, **type_data})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_data['type_name']}` добавлен"}

    elif action == "get" and type_id:
        query = text("SELECT * FROM quest_types WHERE type_id = :type_id")
        result = await db_session.execute(query, {"type_id": type_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Тип квеста не найден"}

    elif action == "update" and type_id and type_data:
        updates = ", ".join(f"{key} = :{key}" for key in type_data.keys())
        query = text(f"""
            UPDATE quest_types SET {updates} WHERE type_id = :type_id
        """)
        await db_session.execute(query, {"type_id": type_id, **type_data})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_id}` обновлён"}

    elif action == "delete" and type_id:
        query = text("DELETE FROM quest_types WHERE type_id = :type_id")
        await db_session.execute(query, {"type_id": type_id})
        await db_session.commit()
        return {"status": "success", "message": f"Тип `{type_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_conditions(action: str, condition_id: int = None, condition_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_conditions`."""
    if action == "insert" and condition_data:
        query = text("""
            INSERT INTO quest_conditions (condition_id, condition_key, condition_name)
            VALUES (:condition_id, :condition_key, :condition_name)
        """)
        await db_session.execute(query, {"condition_id": condition_id, **condition_data})
        await db_session.commit()
        return {"status": "success", "message": f"Условие `{condition_data['condition_key']}` добавлено"}

    elif action == "get" and condition_id:
        query = text("SELECT * FROM quest_conditions WHERE condition_id = :condition_id")
        result = await db_session.execute(query, {"condition_id": condition_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Условие не найдено"}

    elif action == "update" and condition_id and condition_data:
        updates = ", ".join(f"{key} = :{key}" for key in condition_data.keys())
        query = text(f"""
            UPDATE quest_conditions SET {updates} WHERE condition_id = :condition_id
        """)
        await db_session.execute(query, {"condition_id": condition_id, **condition_data})
        await db_session.commit()
        return {"status": "success", "message": f"Условие `{condition_id}` обновлено"}

    elif action == "delete" and condition_id:
        query = text("DELETE FROM quest_conditions WHERE condition_id = :condition_id")
        await db_session.execute(query, {"condition_id": condition_id})
        await db_session.commit()
        return {"status": "success", "message": f"Условие `{condition_id}` удалено"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_requirements(action: str, requirement_id: int = None, requirement_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_requirements`."""
    if action == "insert" and requirement_data:
        query = text("""
            INSERT INTO quest_requirements (requirement_id, requirement_key, requirement_name, requirement_value)
            VALUES (:requirement_id, :requirement_key, :requirement_name, :requirement_value)
        """)
        await db_session.execute(query, {"requirement_id": requirement_id, **requirement_data})
        await db_session.commit()
        return {"status": "success", "message": f"Требование `{requirement_data['requirement_key']}` добавлено"}

    elif action == "get" and requirement_id:
        query = text("SELECT * FROM quest_requirements WHERE requirement_id = :requirement_id")
        result = await db_session.execute(query, {"requirement_id": requirement_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Требование не найдено"}

    elif action == "update" and requirement_id and requirement_data:
        updates = ", ".join(f"{key} = :{key}" for key in requirement_data.keys())
        query = text(f"""
            UPDATE quest_requirements SET {updates} WHERE requirement_id = :requirement_id
        """)
        await db_session.execute(query, {"requirement_id": requirement_id, **requirement_data})
        await db_session.commit()
        return {"status": "success", "message": f"Требование `{requirement_id}` обновлено"}

    elif action == "delete" and requirement_id:
        query = text("DELETE FROM quest_requirements WHERE requirement_id = :requirement_id")
        await db_session.execute(query, {"requirement_id": requirement_id})
        await db_session.commit()
        return {"status": "success", "message": f"Требование `{requirement_id}` удалено"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_quest_rewards(action: str, reward_id: int = None, reward_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `quest_rewards`."""
    if action == "insert" and reward_data:
        query = text("""
            INSERT INTO quest_rewards (id, reward_key, reward_name, reward_value, reward_type, reward_description)
            VALUES (:id, :reward_key, :reward_name, :reward_value, :reward_type, :reward_description)
        """)
        await db_session.execute(query, {"id": reward_id, **reward_data})
        await db_session.commit()
        return {"status": "success", "message": f"Награда `{reward_data['reward_name']}` добавлена"}

    elif action == "get" and reward_id:
        query = text("SELECT * FROM quest_rewards WHERE id = :reward_id")
        result = await db_session.execute(query, {"reward_id": reward_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Награда не найдена"}

    elif action == "update" and reward_id and reward_data:
        updates = ", ".join(f"{key} = :{key}" for key in reward_data.keys())
        query = text(f"""
            UPDATE quest_rewards SET {updates} WHERE id = :reward_id
        """)
        await db_session.execute(query, {"reward_id": reward_id, **reward_data})
        await db_session.commit()
        return {"status": "success", "message": f"Награда `{reward_id}` обновлена"}

    elif action == "delete" and reward_id:
        query = text("DELETE FROM quest_rewards WHERE id = :reward_id")
        await db_session.execute(query, {"reward_id": reward_id})
        await db_session.commit()
        return {"status": "success", "message": f"Награда `{reward_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры"}
