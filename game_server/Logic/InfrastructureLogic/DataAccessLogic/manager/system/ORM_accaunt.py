from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.database.models.models import AccountInfo


class AccountInfoManager:
    """Менеджер для работы с `account_info` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_account(self, account_data: dict):
        """Создание нового аккаунта."""
        account = AccountInfo(**account_data)
        self.db_session.add(account)
        await self.db_session.commit()
        return {"status": "success", "message": f"Аккаунт `{account_data['username']}` создан"}

    async def get_account(self, account_id: int):
        """Получение данных аккаунта по `account_id`."""
        query = select(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self.db_session.execute(query)
        account = result.scalar()
        return {"status": "found", "data": account.__dict__} if account else {"status": "error", "message": "Аккаунт не найден"}

    async def get_account_by_identifier(self, identifier_type: str, identifier_value: str):
        """Поиск аккаунта по переданному идентификатору."""
        query = select(AccountInfo).where(getattr(AccountInfo, identifier_type) == identifier_value)
        result = await self.db_session.execute(query)
        return result.scalar()

    async def update_account(self, account_id: int, update_data: dict):
        """Обновление данных аккаунта."""
        query = select(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self.db_session.execute(query)
        account = result.scalar()

        if account:
            for key, value in update_data.items():
                setattr(account, key, value)
            await self.db_session.commit()
            return {"status": "success", "message": f"Аккаунт `{account_id}` обновлен"}
        return {"status": "error", "message": "Аккаунт не найден"}

    async def delete_account(self, account_id: int):
        """Удаление аккаунта."""
        query = select(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self.db_session.execute(query)
        account = result.scalar()

        if account:
            await self.db_session.delete(account)
            await self.db_session.commit()
            return {"status": "success", "message": f"Аккаунт `{account_id}` удалён"}
        return {"status": "error", "message": "Аккаунт не найден"}
