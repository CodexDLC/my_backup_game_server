from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import AccountInfo, Character





class AccountIdentifiers:
    """Класс для поиска `character_id` по любому идентификатору (`discord_id`, `google_id`, `telegram_id` и т. д.)."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_character_id(self, identifier_type: str, identifier_value: str):
        """
        Универсальная функция поиска `character_id` по любому идентификатору (`discord_id`, `google_id` и т. д.).
        
        :param identifier_type: Тип идентификатора (`discord_id`, `google_id`, `telegram_id` и т. д.).
        :param identifier_value: Значение идентификатора (например, ID из Discord).
        """
        
        # 🔹 Запрашиваем `account_id` по переданному идентификатору
        query = select(AccountInfo).where(getattr(AccountInfo, identifier_type) == identifier_value)
        result = await self.db_session.execute(query)
        account = result.scalar()

        if not account:
            return None  # ❌ Аккаунт не найден
        
        account_id = account.account_id

        # 🔹 Запрашиваем `character_id`, который принадлежит `account_id` и `status='online'`
        query = select(Character).where((Character.account_id == account_id) & (Character.status == "online"))
        result = await self.db_session.execute(query)
        character = result.scalar()

        return character.character_id if character else None  # ❌ Если персонаж не найден, возвращаем None
