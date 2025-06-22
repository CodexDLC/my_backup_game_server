# game_server/Logic/DomainLogic/dom_utils/account_identifiers.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import AccountInfo, Character

class AccountIdentifiers:
    """Класс для поиска ID по внешним идентификаторам."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_account_id(self, identifier_type: str, identifier_value: str) -> int | None:
        """
        Находит и возвращает account_id по указанному типу и значению идентификатора.
        """
        query = select(AccountInfo.account_id).where(getattr(AccountInfo, identifier_type) == identifier_value)
        result = await self.db_session.execute(query)
        account_id = result.scalar_one_or_none()
        return account_id

    async def get_character_id(self, identifier_type: str, identifier_value: str):
        """
        Универсальная функция поиска `character_id` по любому идентификатору (`discord_id`, `google_id` и т. д.).
        """
        account_id = await self.get_account_id(identifier_type, identifier_value)
        if not account_id:
            return None

        query = select(Character.character_id).where(
            (Character.account_id == account_id) & (Character.status == "online")
        )
        result = await self.db_session.execute(query)
        character_id = result.scalar_one_or_none()
        return character_id