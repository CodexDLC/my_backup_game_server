from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

async def manage_account_info(action: str, account_id: int = None, account_data: dict = None, db_session: AsyncSession = None):
    """CRUD-функция для `account_info` (INSERT, SELECT, UPDATE, DELETE) через чистые SQL-запросы."""

    if action == "insert" and account_data:
        query = text("""
            INSERT INTO account_info (username, email, password_hash, google_id, discord_id, telegram_id, twitter_id, steam_id, twitch_id, game_id, platform, linked_platforms, auth_token, avatar, locale, region, status, role, twofa_enabled, created_at, updated_at, last_login)
            VALUES (:username, :email, :password_hash, :google_id, :discord_id, :telegram_id, :twitter_id, :steam_id, :twitch_id, :game_id, :platform, :linked_platforms, :auth_token, :avatar, :locale, :region, :status, :role, :twofa_enabled, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :last_login)
        """)
        await db_session.execute(query, account_data)
        await db_session.commit()
        return {"status": "success", "message": f"Аккаунт `{account_data['username']}` создан"}

    elif action == "get" and account_id:
        query = text("SELECT * FROM account_info WHERE account_id = :account_id")
        result = await db_session.execute(query, {"account_id": account_id})
        row = result.fetchone()
        return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Аккаунт не найден"}

    elif action == "update" and account_id and account_data:
        updates = ", ".join(f"{key} = :{key}" for key in account_data.keys())
        query = text(f"UPDATE account_info SET {updates}, updated_at = CURRENT_TIMESTAMP WHERE account_id = :account_id")
        await db_session.execute(query, {"account_id": account_id, **account_data})
        await db_session.commit()
        return {"status": "success", "message": f"Аккаунт `{account_id}` обновлён"}

    elif action == "delete" and account_id:
        query = text("DELETE FROM account_info WHERE account_id = :account_id")
        await db_session.execute(query, {"account_id": account_id})
        await db_session.commit()
        return {"status": "success", "message": f"Аккаунт `{account_id}` удалён"}

    return {"status": "error", "message": "Неверные параметры запроса"}
