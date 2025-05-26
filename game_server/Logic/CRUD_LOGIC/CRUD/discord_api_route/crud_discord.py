

from sqlalchemy import text
from game_server.Logic.DataAccessLogic.db_instance import AsyncSession


async def manage_discord_bindings(action: str, guild_id: int = None, binding_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `discord_bindings`."""
    if action == "insert" and binding_data:
        query = text("""
            INSERT INTO discord_bindings (guild_id, world_id, entity_access_key, category_id, channel_id, permissions, created_at, updated_at)
            VALUES (:guild_id, :world_id, :entity_access_key, :category_id, :channel_id, :permissions, NOW(), NOW())
        """)
        await db_session.execute(query, {"guild_id": guild_id, **binding_data})
        await db_session.commit()
        return {"status": "success", "message": f"Связь для `{guild_id}` добавлена"}

    elif action == "get" and guild_id:
        query = text("SELECT * FROM discord_bindings WHERE guild_id = :guild_id")
        result = await db_session.execute(query, {"guild_id": guild_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Связь не найдена"}

    elif action == "update" and guild_id and binding_data:
        updates = ", ".join(f"{key} = :{key}" for key in binding_data.keys())
        query = text(f"""
            UPDATE discord_bindings SET {updates}, updated_at = NOW() WHERE guild_id = :guild_id
        """)
        await db_session.execute(query, {"guild_id": guild_id, **binding_data})
        await db_session.commit()
        return {"status": "success", "message": f"Связь `{guild_id}` обновлена"}

    elif action == "delete" and guild_id:
        query = text("DELETE FROM discord_bindings WHERE guild_id = :guild_id")
        await db_session.execute(query, {"guild_id": guild_id})
        await db_session.commit()
        return {"status": "success", "message": f"Связь `{guild_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры запроса"}


async def manage_applied_permissions(action: str, guild_id: int = None, permission_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `applied_permissions`."""
    if action == "insert" and permission_data:
        query = text("""
            INSERT INTO applied_permissions (guild_id, entity_access_key, access_code, target_type, target_id, role_id, applied_at)
            VALUES (:guild_id, :entity_access_key, :access_code, :target_type, :target_id, :role_id, NOW())
        """)
        await db_session.execute(query, {"guild_id": guild_id, **permission_data})
        await db_session.commit()
        return {"status": "success", "message": f"Права `{guild_id}` добавлены"}

    elif action == "get" and guild_id:
        query = text("SELECT * FROM applied_permissions WHERE guild_id = :guild_id")
        result = await db_session.execute(query, {"guild_id": guild_id})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Права не найдены"}

    elif action == "update" and guild_id and permission_data:
        updates = ", ".join(f"{key} = :{key}" for key in permission_data.keys())
        query = text(f"""
            UPDATE applied_permissions SET {updates} WHERE guild_id = :guild_id
        """)
        await db_session.execute(query, {"guild_id": guild_id, **permission_data})
        await db_session.commit()
        return {"status": "success", "message": f"Права `{guild_id}` обновлены"}

    elif action == "delete" and guild_id:
        query = text("DELETE FROM applied_permissions WHERE guild_id = :guild_id")
        await db_session.execute(query, {"guild_id": guild_id})
        await db_session.commit()
        return {"status": "success", "message": f"Права `{guild_id}` удалены"}

    return {"status": "error", "message": "Неверные параметры запроса"}

async def manage_state_entities_discord(action: str, guild_id: int = None, entity_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `state_entities_discord`."""
    if action == "insert" and entity_data:
        query = text("""
            INSERT INTO state_entities_discord (guild_id, world_id, access_code, role_name, role_id, permissions, created_at, updated_at)
            VALUES (:guild_id, :world_id, :access_code, :role_name, :role_id, :permissions, NOW(), NOW())
        """)
        await db_session.execute(query, {"guild_id": guild_id, **entity_data})
        await db_session.commit()
        return {"status": "success", "message": f"Роль `{entity_data['role_name']}` добавлена для гильдии `{guild_id}`"}

    elif action == "get" and guild_id:
        query = text("SELECT * FROM state_entities_discord WHERE guild_id = :guild_id")
        result = await db_session.execute(query, {"guild_id": guild_id})
        rows = result.fetchall()
        return {"status": "found", "data": [dict(row) for row in rows]} if rows else {"status": "error", "message": "Данные не найдены"}

    elif action == "update" and guild_id and entity_data:
        updates = ", ".join(f"{key} = :{key}" for key in entity_data.keys())
        query = text(f"""
            UPDATE state_entities_discord SET {updates}, updated_at = NOW() WHERE guild_id = :guild_id
        """)
        await db_session.execute(query, {"guild_id": guild_id, **entity_data})
        await db_session.commit()
        return {"status": "success", "message": f"Роль `{entity_data['role_name']}` обновлена для `{guild_id}`"}

    elif action == "delete" and guild_id:
        query = text("DELETE FROM state_entities_discord WHERE guild_id = :guild_id")
        await db_session.execute(query, {"guild_id": guild_id})
        await db_session.commit()
        return {"status": "success", "message": f"Роль `{guild_id}` удалена"}

    return {"status": "error", "message": "Неверные параметры"}


async def manage_discord_quest_descriptions(action: str, description_key: str = None, quest_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `discord_quest_descriptions`."""
    if action == "insert" and quest_data:
        query = text("""
            INSERT INTO discord_quest_descriptions (description_key, text)
            VALUES (:description_key, :text)
        """)
        await db_session.execute(query, {"description_key": description_key, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{description_key}` добавлен"}

    elif action == "get" and description_key:
        query = text("SELECT * FROM discord_quest_descriptions WHERE description_key = :description_key")
        result = await db_session.execute(query, {"description_key": description_key})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Квест не найден"}

    elif action == "update" and description_key and quest_data:
        updates = ", ".join(f"{key} = :{key}" for key in quest_data.keys())
        query = text(f"""
            UPDATE discord_quest_descriptions SET {updates} WHERE description_key = :description_key
        """)
        await db_session.execute(query, {"description_key": description_key, **quest_data})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{description_key}` обновлён"}

    elif action == "delete" and description_key:
        query = text("DELETE FROM discord_quest_descriptions WHERE description_key = :description_key")
        await db_session.execute(query, {"description_key": description_key})
        await db_session.commit()
        return {"status": "success", "message": f"Квест `{description_key}` удалён"}

    return {"status": "error", "message": "Неверные параметры"}
