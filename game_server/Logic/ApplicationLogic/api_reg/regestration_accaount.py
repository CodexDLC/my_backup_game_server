import secrets
from sqlalchemy import update

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.ORM_accaunt import AccountInfoManager
from game_server.settings import REGISTRATION_URL

class CreateAccountManager:
    def __init__(self):
        """Создаёт `db_session`, чтобы все методы могли её использовать"""
        self.db_session = AsyncSessionLocal()  # 🔥 Теперь сессия общая для всех функций
        self.manager = AccountInfoManager(self.db_session)

    async def create_account(self, identifier_type: str, identifier_value: str, username: str, avatar: str = None, locale: str = None, region: str = None):
        """
        Создаёт новый аккаунт или привязывает новую платформу, если аккаунт уже существует.
        """
        existing_account = await self.manager.get_account_by_identifier(identifier_type, identifier_value)

        if existing_account:
            linked_platforms = existing_account.linked_platforms or {}
            linked_platforms[identifier_type] = identifier_value

            if not existing_account.auth_token:
                existing_account.auth_token = secrets.token_hex(32)
                await self.manager.update_account(existing_account.account_id, {"auth_token": existing_account.auth_token})

            await self.manager.update_account(existing_account.account_id, {"linked_platforms": linked_platforms})
            await self.db_session.commit()  # 🔥 Подтверждаем изменения
            return {"status": "updated", "account_id": existing_account.account_id, "auth_token": existing_account.auth_token}

        auth_token = secrets.token_hex(32)
        account_data = {
            "username": username,
            "avatar": avatar,
            "locale": locale,
            "region": region,
            "status": "active",
            "role": "user",
            "twofa_enabled": False,
            "auth_token": auth_token,
            "linked_platforms": {identifier_type: identifier_value},
        }

        new_account = await self.manager.create_account(account_data)
        await self.db_session.commit()  # 🔥 Подтверждаем транзакцию
        return {"status": "created", "account_id": new_account["account_id"], "auth_token": auth_token}

    async def close_session(self):
        """Корректное закрытие `db_session`"""
        await self.db_session.close()  # 🔥 Закрываем соединение вручную после использования класса

    async def update_account(self, identifier_type: str, identifier_value: str, update_data: dict):
        """
        Обновляет данные аккаунта по `identifier_type`.
        """
        existing_account = await self.manager.get_account_by_identifier(identifier_type, identifier_value)

        if not existing_account:
            return {"status": "error", "message": "Аккаунт не найден"}

        return await self.manager.update_account(existing_account.account_id, update_data)

    async def delete_account(self, identifier_type: str, identifier_value: str):
        """
        Удаляет аккаунт по `identifier_type`.
        """
        existing_account = await self.manager.get_account_by_identifier(identifier_type, identifier_value)

        if not existing_account:
            return {"status": "error", "message": "Аккаунт не найден"}

        return await self.manager.delete_account(existing_account.account_id)

    async def generate_registration_link(self, identifier_type: str, identifier_value: str):
        """
        Генерирует ссылку для регистрации, используя `auth_token` аккаунта.
        """
        existing_account = await self.manager.get_account_by_identifier(identifier_type, identifier_value)

        if not existing_account:
            return {"status": "error", "message": "Аккаунт не найден"}

        auth_token = existing_account.auth_token

        # 🔥 Формируем ссылку для регистрации из `.env`
        registration_link = f"{REGISTRATION_URL}{auth_token}"

        return {"status": "success", "registration_link": registration_link}