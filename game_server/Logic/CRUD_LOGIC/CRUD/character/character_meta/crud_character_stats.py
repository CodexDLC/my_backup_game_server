







from sqlalchemy import text
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession



async def manage_character_stats(action: str, character_id: int, table_name: str, stats: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы со статами персонажа (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param character_id: ID персонажа.
    :param table_name: Название таблицы, с которой работаем (characters_special, player_status и т. д.).
    :param stats: Словарь характеристик (для insert и update).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and stats:
        fields = ", ".join(stats.keys())  
        placeholders = ", ".join(f":{key}" for key in stats.keys())  
        query = text(f"""
            INSERT INTO {table_name} (character_id, {fields})
            VALUES (:character_id, {placeholders})
        """)
        await db_session.execute(query, {"character_id": character_id, **stats})
        await db_session.commit()
        return {"status": "success", "message": f"Статы персонажа {character_id} записаны в {table_name}"}

    elif action == "get":
        query = text(f"SELECT * FROM {table_name} WHERE character_id = :character_id")
        result = await db_session.execute(query, {"character_id": character_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Персонаж не найден"}

    elif action == "update" and stats:
        updates = ", ".join(f"{key} = :{key}" for key in stats.keys())  
        query = text(f"""
            UPDATE {table_name} SET {updates}, updated_at = CURRENT_TIMESTAMP
            WHERE character_id = :character_id
        """)
        await db_session.execute(query, {"character_id": character_id, **stats})
        await db_session.commit()
        return {"status": "success", "message": "Статы персонажа обновлены"}

    elif action == "delete":
        query = text(f"DELETE FROM {table_name} WHERE character_id = :character_id")
        await db_session.execute(query, {"character_id": character_id})
        await db_session.commit()
        return {"status": "success", "message": "Статы персонажа удалены"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_special_stat_effects(action: str, stat_key: str = None, effect_data: dict = None, db_session: AsyncSession = None):
    """
    Универсальная функция для работы с таблицей `special_stat_effects` (INSERT, SELECT, UPDATE, DELETE).

    :param action: Действие ("insert", "get", "update", "delete").
    :param stat_key: Ключ статового эффекта (нужно для "get", "update", "delete").
    :param effect_data: Данные для записи/обновления (например, {"effect_field": "combat_boost", "multiplier": 1.5}).
    :param db_session: Асинхронная сессия базы данных.
    :return: Результат операции.
    """

    if action == "insert" and effect_data:
        query = text("""
            INSERT INTO special_stat_effects (stat_key, effect_field, multiplier, description)
            VALUES (:stat_key, :effect_field, :multiplier, :description)
        """)
        await db_session.execute(query, {"stat_key": stat_key, **effect_data})
        await db_session.commit()
        return {"status": "success", "message": f"Статовый эффект `{stat_key}` добавлен"}

    elif action == "get" and stat_key:
        query = text("SELECT * FROM special_stat_effects WHERE stat_key = :stat_key")
        result = await db_session.execute(query, {"stat_key": stat_key})
        effect = result.fetchone()
        return {"status": "found", "data": dict(effect)} if effect else {"status": "error", "message": "Эффект не найден"}

    elif action == "update" and stat_key and effect_data:
        update_query = text("""
            UPDATE special_stat_effects SET effect_field = :effect_field, multiplier = :multiplier, description = :description
            WHERE stat_key = :stat_key
        """)
        await db_session.execute(update_query, {"stat_key": stat_key, **effect_data})
        await db_session.commit()
        return {"status": "success", "message": f"Статовый эффект `{stat_key}` обновлён"}

    elif action == "delete" and stat_key:
        delete_query = text("DELETE FROM special_stat_effects WHERE stat_key = :stat_key")
        await db_session.execute(delete_query, {"stat_key": stat_key})
        await db_session.commit()
        return {"status": "success", "message": f"Статовый эффект `{stat_key}` удалён"}

    return {"status": "error", "message": "Неверные параметры запроса"}
