


from sqlalchemy import text


async def create_account_from_discord(discord_id: str, username: str, avatar: str, locale: str, region: str, db_session):
    """
    Создает аккаунт в базе данных, если `discord_id` отсутствует.

    :param discord_id: Discord ID пользователя.
    :param username: Имя пользователя в Discord.
    :param avatar: Ссылка на аватар.
    :param locale: Язык пользователя.
    :param region: Регион пользователя.
    :param db_session: Сессия базы данных.
    """
    # Проверяем, есть ли аккаунт с таким discord_id
    query_check = text("SELECT account_id FROM account_info WHERE discord_id = :discord_id")
    result = await db_session.execute(query_check, {"discord_id": discord_id})
    existing_account = result.fetchone()

    if existing_account:
        return {"status": "exists", "account_id": existing_account["account_id"]}

    # Создаем новый аккаунт
    query_insert = text("""
        INSERT INTO account_info (discord_id, username, avatar, locale, region)
        VALUES (:discord_id, :username, :avatar, :locale, :region)
        RETURNING account_id
    """)
    result = await db_session.execute(query_insert, {
        "discord_id": discord_id,
        "username": username,
        "avatar": avatar,
        "locale": locale,
        "region": region
    })
    await db_session.commit()
    
    new_account_id = result.fetchone()["account_id"]
    return {"status": "created", "account_id": new_account_id}
