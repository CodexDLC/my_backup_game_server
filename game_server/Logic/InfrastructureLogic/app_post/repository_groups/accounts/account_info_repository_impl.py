# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/account_info_repository_impl.py

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func, String, update, delete
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy.exc import IntegrityError, NoResultFound

# Убедитесь, что путь к вашей модели AccountInfo корректен
from game_server.database.models.models import AccountInfo

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class AccountInfoRepositoryImpl(IAccountInfoRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью AccountInfo.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """

    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_account(self, account_data: Dict[str, Any]) -> AccountInfo:
        """
        Создает новый аккаунт.
        """
        # Проверяем уникальность username
        if "username" in account_data:
            # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию для проверки
            existing_by_username = await self.get_account_by_username(account_data["username"])
            if existing_by_username:
                raise ValueError(f"Username '{account_data['username']}' already exists.")

        # Проверяем уникальность email (если он есть и не None)
        if "email" in account_data and account_data["email"] is not None:
            # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию для проверки
            existing_by_email = await self.get_account_by_email(account_data["email"])
            if existing_by_email:
                raise ValueError(f"Email '{account_data['email']}' already exists.")

        new_account = AccountInfo(**account_data)
        self._session.add(new_account)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Аккаунт '{new_account.username}' (ID: {new_account.account_id}) добавлен в сессию.")
        return new_account

    async def get_account_by_id(self, account_id: int) -> Optional[AccountInfo]:
        """Получение данных аккаунта по `account_id`."""
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_username(self, username: str) -> Optional[AccountInfo]:
        """Получает аккаунт по имени пользователя."""
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo).where(AccountInfo.username == username)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_email(self, email: str) -> Optional[AccountInfo]:
        """Получает аккаунт по email."""
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo).where(AccountInfo.email == email)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_identifier(self, identifier_type: str, identifier_value: str) -> Optional[AccountInfo]:
        """
        Поиск аккаунта по переданному идентификатору в `linked_platforms` (JSON).
        """
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo).where(
            func.json_extract_path_text(AccountInfo.linked_platforms, identifier_type) == identifier_value
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def update_account(self, account_id: int, update_data: Dict[str, Any]) -> Optional[AccountInfo]:
        """
        Обновление данных аккаунта.
        """
        # 🔥 ИЗМЕНЕНИЕ: Получаем аккаунт в текущей сессии
        stmt = fselect(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self._session.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            logger.warning(f"Аккаунт с ID {account_id} не найден для обновления в текущей сессии.")
            return None

        for key, value in update_data.items():
            if key == "linked_platforms" and isinstance(value, dict):
                current_linked_platforms = account.linked_platforms or {}
                current_linked_platforms.update(value)
                setattr(account, key, current_linked_platforms)
            else:
                setattr(account, key, value)

        account.updated_at = datetime.now(timezone.utc)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Аккаунт {account_id} обновлен в сессии.")
        return account

    async def delete_account(self, account_id: int) -> bool:
        """
        Удаление аккаунта.
        """
        # 🔥 ИЗМЕНЕНИЕ: Получаем аккаунт в текущей сессии
        stmt = fselect(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self._session.execute(stmt)
        account_to_delete = result.scalar_one_or_none()
        if not account_to_delete:
            logger.warning(f"Аккаунт с ID {account_id} не найден для удаления в текущей сессии.")
            return False

        await self._session.delete(account_to_delete)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Аккаунт {account_id} помечен для удаления в сессии.")
        return True

    async def get_all_guest_usernames(self) -> List[str]:
        """Получает список всех имен пользователей, начинающихся с "Гость"."""
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo.username).where(AccountInfo.username.like("Гость%"))
        result = await self._session.execute(query)
        return [u for u, in result.scalars().all()]

    async def get_account_by_auth_token(self, auth_token: str) -> Optional[AccountInfo]:
        """Получает аккаунт по токену аутентификации."""
        # 🔥 ИЗМЕНЕНИЕ: Используем текущую сессию
        query = fselect(AccountInfo).where(AccountInfo.auth_token == auth_token)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
