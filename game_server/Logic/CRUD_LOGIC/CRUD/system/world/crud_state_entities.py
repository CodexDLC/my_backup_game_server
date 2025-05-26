from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def manage_entity_properties(action: str, entity_id: str = None, property_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `entity_properties` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param entity_id: ID сущности (нужно для "get", "update", "delete").
    :param property_data: Данные для записи/обновления (например, {"key": "speed", "value": "10"}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and property_data:
        query = text("""
            INSERT INTO entity_properties (id, entity_type, entity_id, key, value)
            VALUES (gen_random_uuid(), :entity_type, :entity_id, :key, :value)
        """)
        await db_session.execute(query, {"entity_id": entity_id, **property_data})
        await db_session.commit()
        return {"status": "success", "message": f"Параметр `{property_data['key']}` добавлен для сущности `{entity_id}`"}

    elif action == "get" and entity_id:
        query = text("SELECT * FROM entity_properties WHERE entity_id = :entity_id")
        result = await db_session.execute(query, {"entity_id": entity_id})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Параметры не найдены"}

    elif action == "update" and entity_id and property_data:
        query = text("""
            UPDATE entity_properties SET value = :value
            WHERE entity_id = :entity_id AND key = :key
        """)
        await db_session.execute(query, {"entity_id": entity_id, "key": property_data["key"], "value": property_data["value"]})
        await db_session.commit()
        return {"status": "success", "message": f"Параметр `{property_data['key']}` обновлён для сущности `{entity_id}`"}

    elif action == "delete" and entity_id:
        query = text("DELETE FROM entity_properties WHERE entity_id = :entity_id")
        await db_session.execute(query, {"entity_id": entity_id})
        await db_session.commit()
        return {"status": "success", "message": f"Параметры сущности `{entity_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_entity_state_map(action: str, entity_access_key: str = None, state_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `entity_state_map` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param entity_access_key: Уникальный ключ сущности (нужно для "get", "update", "delete").
    :param state_data: Данные для записи/обновления (например, {"access_code": 101}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and state_data:
        query = text("""
            INSERT INTO entity_state_map (entity_access_key, access_code)
            VALUES (:entity_access_key, :access_code)
        """)
        await db_session.execute(query, {"entity_access_key": entity_access_key, **state_data})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['access_code']}` привязано к `{entity_access_key}`"}

    elif action == "get" and entity_access_key:
        query = text("SELECT * FROM entity_state_map WHERE entity_access_key = :entity_access_key")
        result = await db_session.execute(query, {"entity_access_key": entity_access_key})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Состояния не найдены"}

    elif action == "update" and entity_access_key and state_data:
        query = text("""
            UPDATE entity_state_map SET access_code = :access_code
            WHERE entity_access_key = :entity_access_key
        """)
        await db_session.execute(query, {"entity_access_key": entity_access_key, **state_data})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['access_code']}` обновлено для `{entity_access_key}`"}

    elif action == "delete" and entity_access_key:
        query = text("DELETE FROM entity_state_map WHERE entity_access_key = :entity_access_key")
        await db_session.execute(query, {"entity_access_key": entity_access_key})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние сущности `{entity_access_key}` удалено"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_state_entities(action: str, access_code: int = None, state_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `state_entities` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param access_code: Код состояния (нужно для "get", "update", "delete").
    :param state_data: Данные для записи/обновления (например, {"code_name": "Poisoned", "ui_type": "effect"}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and state_data:
        query = text("""
            INSERT INTO state_entities (id, access_code, code_name, ui_type, description, is_active)
            VALUES (DEFAULT, :access_code, :code_name, :ui_type, :description, :is_active)
        """)
        await db_session.execute(query, {"access_code": access_code, **state_data})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['code_name']}` добавлено"}

    elif action == "get" and access_code:
        query = text("SELECT * FROM state_entities WHERE access_code = :access_code")
        result = await db_session.execute(query, {"access_code": access_code})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Состояние не найдено"}

    elif action == "update" and access_code and state_data:
        query = text("""
            UPDATE state_entities SET code_name = :code_name, ui_type = :ui_type, description = :description, is_active = :is_active
            WHERE access_code = :access_code
        """)
        await db_session.execute(query, {"access_code": access_code, **state_data})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['code_name']}` обновлено"}

    elif action == "delete" and access_code:
        query = text("DELETE FROM state_entities WHERE access_code = :access_code")
        await db_session.execute(query, {"access_code": access_code})
        await db_session.commit()
        return {"status": "success", "message": f"Состояние `{access_code}` удалено"}

    return {"status": "error", "message": "Неверные параметры запроса"}
