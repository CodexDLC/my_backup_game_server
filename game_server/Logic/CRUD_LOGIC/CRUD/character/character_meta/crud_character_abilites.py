

# game_server\Logic\CRUD_LOGIC\CRUD\character\crud_character_abilites.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def manage_abilities(action: str, ability_key: str = None, ability_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `abilities` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param ability_key: Уникальный ключ способности (нужно для "get", "update", "delete").
    :param ability_data: Данные для вставки/обновления (например, {"ability_type": "magic", "params": {}}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and ability_data:
        query = text("""
            INSERT INTO abilities (ability_key, ability_type, params, description)
            VALUES (:ability_key, :ability_type, :params, :description)
        """)
        await db_session.execute(query, {"ability_key": ability_key, **ability_data})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` добавлена"}

    elif action == "get" and ability_key:
        query = text("SELECT * FROM abilities WHERE ability_key = :ability_key")
        result = await db_session.execute(query, {"ability_key": ability_key})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Способность не найдена"}

    elif action == "update" and ability_key and ability_data:
        updates = ", ".join(f"{key} = :{key}" for key in ability_data.keys())
        query = text(f"""
            UPDATE abilities SET {updates}
            WHERE ability_key = :ability_key
        """)
        await db_session.execute(query, {"ability_key": ability_key, **ability_data})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` обновлена"}

    elif action == "delete" and ability_key:
        query = text("DELETE FROM abilities WHERE ability_key = :ability_key")
        await db_session.execute(query, {"ability_key": ability_key})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` удалена"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_skill_ability_unlocks(action: str, skill_key: str = None, level: int = None, ability_key: str = None, unlock_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `skill_ability_unlocks` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param skill_key: Ключ навыка (нужно для "get", "update", "delete").
    :param level: Уровень разблокировки (можно использовать для "get").
    :param ability_key: Ключ способности (нужно для "get", "update", "delete").
    :param unlock_data: Данные для вставки/обновления (например, {"ability_key": "fireball"}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and skill_key and level and ability_key:
        query = text("""
            INSERT INTO skill_ability_unlocks (skill_key, level, ability_key)
            VALUES (:skill_key, :level, :ability_key)
        """)
        await db_session.execute(query, {"skill_key": skill_key, "level": level, "ability_key": ability_key})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` для `{skill_key}` (уровень {level}) добавлена"}

    elif action == "get":
        conditions, params = [], {}

        if skill_key:
            conditions.append("skill_key = :skill_key")
            params["skill_key"] = skill_key
        if level:
            conditions.append("level = :level")
            params["level"] = level
        if ability_key:
            conditions.append("ability_key = :ability_key")
            params["ability_key"] = ability_key

        condition_str = " AND ".join(conditions) if conditions else "TRUE"

        query = text(f"SELECT * FROM skill_ability_unlocks WHERE {condition_str}")
        result = await db_session.execute(query, params)
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Способности не найдены"}

    elif action == "update" and skill_key and level and ability_key and unlock_data:
        updates = ", ".join(f"{key} = :{key}" for key in unlock_data.keys())
        query = text(f"""
            UPDATE skill_ability_unlocks SET {updates}
            WHERE skill_key = :skill_key AND level = :level AND ability_key = :ability_key
        """)
        await db_session.execute(query, {"skill_key": skill_key, "level": level, "ability_key": ability_key, **unlock_data})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` обновлена для `{skill_key}` (уровень {level})"}

    elif action == "delete" and skill_key and level and ability_key:
        query = text("DELETE FROM skill_ability_unlocks WHERE skill_key = :skill_key AND level = :level AND ability_key = :ability_key")
        await db_session.execute(query, {"skill_key": skill_key, "level": level, "ability_key": ability_key})
        await db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` удалена из `{skill_key}` (уровень {level})"}

    return {"status": "error", "message": "Неверные параметры запроса"}
