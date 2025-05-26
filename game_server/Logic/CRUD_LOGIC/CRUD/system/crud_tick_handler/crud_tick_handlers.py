


from sqlalchemy import text
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import generate_character_id
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession





async def manage_exploration_chances(action: str, character_id: int, chances_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей character_exploration_chances (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param character_id: ID персонажа.
    :param chances_data: Данные для вставки/обновления (например, {"combat_chance": 0.5, "magic_chance": 0.3}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and chances_data:
        query = text("""
            INSERT INTO character_exploration_chances (character_id, combat_chance, magic_chance, gathering_chance)
            VALUES (:character_id, :combat_chance, :magic_chance, :gathering_chance)
        """)
        await db_session.execute(query, {"character_id": character_id, **chances_data})
        await db_session.commit()
        return {"status": "success", "message": f"Данные шансов исследования добавлены персонажу {character_id}"}

    elif action == "get":
        query = text("SELECT * FROM character_exploration_chances WHERE character_id = :character_id")
        result = await db_session.execute(query, {"character_id": character_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Персонаж не найден"}

    elif action == "update" and chances_data:
        update_query = text("""
            UPDATE character_exploration_chances SET combat_chance = :combat_chance, magic_chance = :magic_chance,
            gathering_chance = :gathering_chance, last_updated = CURRENT_TIMESTAMP
            WHERE character_id = :character_id
        """)
        await db_session.execute(update_query, {"character_id": character_id, **chances_data})
        await db_session.commit()
        return {"status": "success", "message": "Данные шансов исследования обновлены"}

    elif action == "delete":
        query = text("DELETE FROM character_exploration_chances WHERE character_id = :character_id")
        await db_session.execute(query, {"character_id": character_id})
        await db_session.commit()
        return {"status": "success", "message": "Данные шансов исследования удалены"}

    return {"status": "error", "message": "Неверные параметры запроса"}


