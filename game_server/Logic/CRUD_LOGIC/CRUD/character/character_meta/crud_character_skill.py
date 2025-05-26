


from sqlalchemy import text
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import generate_character_id
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def manage_skills(action: str, skill_id: int = None, skill_key: str = None, skill_data: dict = None, skill_group: str = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `skills` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param skill_id: ID навыка (нужно для "get", "update", "delete").
    :param skill_key: Уникальный ключ навыка (можно использовать для "get").
    :param skill_data: Данные для вставки/обновления (например, {"name": "Alchemy", "skill_group": "Magic"}).
    :param skill_group: Группа навыков (для выборки "get").
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and skill_data:
        query = text("""
            INSERT INTO skills (skill_id, skill_key, name, skill_group, main_special, secondary_special)
            VALUES (:skill_id, :skill_key, :name, :skill_group, :main_special, :secondary_special)
        """)
        await db_session.execute(query, skill_data)
        await db_session.commit()
        return {"status": "success", "message": f"Навык `{skill_data['name']}` добавлен"}

    elif action == "get":
        conditions, params = [], {}

        if skill_id:
            conditions.append("skill_id = :skill_id")
            params["skill_id"] = skill_id
        if skill_key:
            conditions.append("skill_key = :skill_key")
            params["skill_key"] = skill_key
        if skill_group:
            conditions.append("skill_group = :skill_group")
            params["skill_group"] = skill_group

        condition_str = " AND ".join(conditions) if conditions else "TRUE"

        query = text(f"SELECT * FROM skills WHERE {condition_str}")
        result = await db_session.execute(query, params)
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Навыки не найдены"}

    elif action == "update" and skill_id and skill_data:
        updates = ", ".join(f"{key} = :{key}" for key in skill_data.keys())
        query = text(f"""
            UPDATE skills SET {updates}
            WHERE skill_id = :skill_id
        """)
        await db_session.execute(query, {"skill_id": skill_id, **skill_data})
        await db_session.commit()
        return {"status": "success", "message": f"Навык `{skill_id}` обновлён"}

    elif action == "delete" and skill_id:
        query = text("DELETE FROM skills WHERE skill_id = :skill_id")
        await db_session.execute(query, {"skill_id": skill_id})
        await db_session.commit()
        return {"status": "success", "message": f"Навык `{skill_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры запроса"}

async def manage_character_skills(action: str, character_id: int, skill_key: int = None, skill_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с навыками персонажа (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param character_id: ID персонажа.
    :param skill_key: Ключ навыка (нужно для "get", "update", "delete").
    :param skill_data: Данные для вставки или обновления (например, {"progress_state": "PLUS"}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and skill_data:
        query = text("""
            INSERT INTO character_skills (character_id, skill_key, progress_state)
            VALUES (:character_id, :skill_key, :progress_state)
        """)
        await db_session.execute(query, {"character_id": character_id, **skill_data})
        await db_session.commit()
        return {"status": "success", "message": f"Навык {skill_key} добавлен персонажу {character_id}"}

    elif action == "get" and skill_key:
        query = text("SELECT * FROM character_skills WHERE character_id = :character_id AND skill_key = :skill_key")
        result = await db_session.execute(query, {"character_id": character_id, "skill_key": skill_key})
        skill = result.fetchone()
        return {"status": "found", "data": dict(skill)} if skill else {"status": "error", "message": "Навык не найден"}

    elif action == "update" and skill_key and skill_data:
        update_query = text("""
            UPDATE character_skills SET progress_state = :progress_state, updated_at = CURRENT_TIMESTAMP
            WHERE character_id = :character_id AND skill_key = :skill_key
        """)
        await db_session.execute(update_query, {"character_id": character_id, "skill_key": skill_key, **skill_data})
        await db_session.commit()
        return {"status": "success", "message": f"Навык {skill_key} у персонажа {character_id} обновлён"}

    elif action == "delete" and skill_key:
        delete_query = text("DELETE FROM character_skills WHERE character_id = :character_id AND skill_key = :skill_key")
        await db_session.execute(delete_query, {"character_id": character_id, "skill_key": skill_key})
        await db_session.commit()
        return {"status": "success", "message": f"Навык {skill_key} у персонажа {character_id} удалён"}

    return {"status": "error", "message": "Неверные параметры запроса"}
