





from sqlalchemy import text
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import generate_character_id
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession


async def manage_character(action: str, account_id: int, db_session: AsyncSession, character_id: int = None, character_data: dict = None):
    """
    Универсальная функция для работы с таблицей characters (создание, извлечение, обновление, удаление).
    
    :param action: Действие ("create", "get", "update", "delete").
    :param account_id: ID аккаунта, к которому привязан персонаж.
    :param db_session: Сессия базы данных.
    :param character_id: ID персонажа (нужно для "get", "update", "delete").
    :param character_data: Данные для обновления (нужно для "update").
    :return: Результат операции.
    """

    if action == "create":
        new_character_id = generate_character_id(account_id)
        query = text("""
            INSERT INTO characters (character_id, account_id, name, surname, bloodline_id, race_id, created_at, updated_at, is_deleted)
            VALUES (:character_id, :account_id, 'Безымянный', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false)
            RETURNING character_id
        """)
        result = await db_session.execute(query, {"character_id": new_character_id, "account_id": account_id})
        await db_session.commit()
        return {"status": "success", "character_id": result.fetchone()["character_id"]}

    elif action == "get" and character_id:
        query = text("SELECT * FROM characters WHERE character_id = :character_id")
        result = await db_session.execute(query, {"character_id": character_id})
        character = result.fetchone()
        return {"status": "found", "data": character} if character else {"status": "error", "message": "Персонаж не найден"}

    elif action == "update" and character_id and character_data:
        update_query = text("""
            UPDATE characters SET name = :name, surname = :surname, bloodline_id = :bloodline_id, race_id = :race_id, updated_at = CURRENT_TIMESTAMP
            WHERE character_id = :character_id
        """)
        await db_session.execute(update_query, {**character_data, "character_id": character_id})
        await db_session.commit()
        return {"status": "success", "message": "Персонаж обновлён"}

    elif action == "delete" and character_id:
        delete_query = text("UPDATE characters SET is_deleted = true WHERE character_id = :character_id")
        await db_session.execute(delete_query, {"character_id": character_id})
        await db_session.commit()
        return {"status": "success", "message": "Персонаж удалён"}

    return {"status": "error", "message": "Неверные параметры запроса"}


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def manage_bloodlines(action: str, bloodline_id: int = None, bloodline_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `bloodlines` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param bloodline_id: ID родословной (нужно для "get", "update", "delete").
    :param bloodline_data: Данные для вставки/обновления (например, {"bloodline_name": "Elf"}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and bloodline_data:
        query = text("""
            INSERT INTO bloodlines (bloodline_id, bloodline_name)
            VALUES (:bloodline_id, :bloodline_name)
        """)
        await db_session.execute(query, {"bloodline_id": bloodline_id, **bloodline_data})
        await db_session.commit()
        return {"status": "success", "message": f"Родословная `{bloodline_data['bloodline_name']}` добавлена"}

    elif action == "get" and bloodline_id:
        query = text("SELECT * FROM bloodlines WHERE bloodline_id = :bloodline_id")
        result = await db_session.execute(query, {"bloodline_id": bloodline_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Родословная не найдена"}

    elif action == "update" and bloodline_id and bloodline_data:
        update_query = text("""
            UPDATE bloodlines SET bloodline_name = :bloodline_name
            WHERE bloodline_id = :bloodline_id
        """)
        await db_session.execute(update_query, {"bloodline_id": bloodline_id, **bloodline_data})
        await db_session.commit()
        return {"status": "success", "message": f"Родословная `{bloodline_id}` обновлена"}

    elif action == "delete" and bloodline_id:
        delete_query = text("DELETE FROM bloodlines WHERE bloodline_id = :bloodline_id")
        await db_session.execute(delete_query, {"bloodline_id": bloodline_id})
        await db_session.commit()
        return {"status": "success", "message": f"Родословная `{bloodline_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_races(action: str, race_id: int = None, race_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `races` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param race_id: ID расы (нужно для "get", "update", "delete").
    :param race_data: Данные для вставки/обновления (например, {"name": "Elf", "founder_id": 2}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and race_data:
        query = text("""
            INSERT INTO races (race_id, name, founder_id)
            VALUES (:race_id, :name, :founder_id)
        """)
        await db_session.execute(query, {"race_id": race_id, **race_data})
        await db_session.commit()
        return {"status": "success", "message": f"Раса `{race_data['name']}` добавлена"}

    elif action == "get" and race_id:
        query = text("SELECT * FROM races WHERE race_id = :race_id")
        result = await db_session.execute(query, {"race_id": race_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Раса не найдена"}

    elif action == "update" and race_id and race_data:
        update_query = text("""
            UPDATE races SET name = :name, founder_id = :founder_id, created_at = CURRENT_TIMESTAMP
            WHERE race_id = :race_id
        """)
        await db_session.execute(update_query, {"race_id": race_id, **race_data})
        await db_session.commit()
        return {"status": "success", "message": f"Раса `{race_id}` обновлена"}

    elif action == "delete" and race_id:
        delete_query = text("DELETE FROM races WHERE race_id = :race_id")
        await db_session.execute(delete_query, {"race_id": race_id})
        await db_session.commit()
        return {"status": "success", "message": f"Раса `{race_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры запроса"}
