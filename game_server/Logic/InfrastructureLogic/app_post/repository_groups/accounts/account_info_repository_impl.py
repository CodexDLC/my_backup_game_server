# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/account_info_repository_impl.py
# (Примечание: после переименования файла на `account_info_repository_impl.py`)

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func, String, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy.exc import IntegrityError, NoResultFound # Добавлены для обработки ошибок

# Убедитесь, что путь к вашей модели AccountInfo корректен
from game_server.database.models.models import AccountInfo

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository # <-- ИМПОРТ ИНТЕРФЕЙСА

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # <-- ИМПОРТ ЛОГГЕРА


class AccountInfoRepositoryImpl(IAccountInfoRepository): # <-- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью AccountInfo.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_account(self, account_data: Dict[str, Any]) -> AccountInfo:
        """
        Создает новый аккаунт.
        :param account_data: Словарь с данными для нового аккаунта.
        :return: Созданный объект AccountInfo.
        :raises ValueError: Если username или email уже занят.
        """
        try:
            # Проверяем уникальность username
            if "username" in account_data:
                existing_by_username = await self.get_account_by_username(account_data["username"])
                if existing_by_username:
                    raise ValueError(f"Username '{account_data['username']}' already exists.")

            # Проверяем уникальность email (если он есть и не None)
            if "email" in account_data and account_data["email"] is not None:
                existing_by_email = await self.get_account_by_email(account_data["email"])
                if existing_by_email:
                    raise ValueError(f"Email '{account_data['email']}' already exists.")

            new_account = AccountInfo(**account_data)
            self.db_session.add(new_account)
            await self.db_session.flush()  # Используем flush, чтобы получить ID нового объекта
            # db_session.commit() не вызывается здесь, т.к. это задача вызывающего кода (сервиса/UoW)
            logger.info(f"Аккаунт '{new_account.username}' (ID: {new_account.account_id}) добавлен в сессию.")
            return new_account
        except IntegrityError as e: # Обработка возможных ошибок уникальности
            logger.error(f"Ошибка целостности при создании аккаунта '{account_data.get('username')}': {e.orig}", exc_info=True)
            raise ValueError(f"Ошибка целостности при создании аккаунта: {e.orig}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при создании аккаунта '{account_data.get('username')}': {e}", exc_info=True)
            raise

    async def get_account_by_id(self, account_id: int) -> Optional[AccountInfo]:
        """Получение данных аккаунта по `account_id`."""
        query = fselect(AccountInfo).where(AccountInfo.account_id == account_id)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_username(self, username: str) -> Optional[AccountInfo]:
        """Получает аккаунт по имени пользователя."""
        query = fselect(AccountInfo).where(AccountInfo.username == username)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_email(self, email: str) -> Optional[AccountInfo]:
        """Получает аккаунт по email."""
        query = fselect(AccountInfo).where(AccountInfo.email == email)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_account_by_identifier(self, identifier_type: str, identifier_value: str) -> Optional[AccountInfo]:
        """
        Поиск аккаунта по переданному идентификатору в `linked_platforms` (JSONB).
        Использует оператор `->>` для извлечения значения.
        """
        query = fselect(AccountInfo).where(
            func.jsonb_extract_path_text(AccountInfo.linked_platforms, identifier_type) == identifier_value
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def update_account(self, account_id: int, update_data: Dict[str, Any]) -> Optional[AccountInfo]:
        """
        Обновление данных аккаунта.
        :param account_id: ID аккаунта для обновления.
        :param update_data: Словарь с полями и их новыми значениями.
        :return: Обновленный объект AccountInfo или None, если аккаунт не найден.
        """
        try:
            account = await self.get_account_by_id(account_id)
            if not account:
                logger.warning(f"Аккаунт с ID {account_id} не найден для обновления.")
                return None

            for key, value in update_data.items():
                if key == "linked_platforms" and isinstance(value, dict):
                    current_linked_platforms = account.linked_platforms or {}
                    current_linked_platforms.update(value)
                    setattr(account, key, current_linked_platforms)
                else:
                    setattr(account, key, value)

            account.updated_at = datetime.now(timezone.utc)
            await self.db_session.flush() # Используем flush
            logger.info(f"Аккаунт {account_id} обновлен в сессии.")
            return account
        except Exception as e:
            logger.error(f"Ошибка при обновлении аккаунта {account_id}: {e}", exc_info=True)
            raise

    async def delete_account(self, account_id: int) -> bool:
        """
        Удаление аккаунта.
        :param account_id: ID аккаунта для удаления.
        :return: True, если аккаунт удален, False в противном случае.
        """
        try:
            account = await self.get_account_by_id(account_id)
            if not account:
                logger.warning(f"Аккаунт с ID {account_id} не найден для удаления.")
                return False

            await self.db_session.delete(account)
            # db_session.commit() не вызывается здесь, ответственность на вызывающем коде
            logger.info(f"Аккаунт {account_id} помечен для удаления в сессии.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении аккаунта {account_id}: {e}", exc_info=True)
            raise

    async def get_all_guest_usernames(self) -> List[str]:
        """Получает список всех имен пользователей, начинающихся с "Гость"."""
        query = fselect(AccountInfo.username).where(AccountInfo.username.like("Гость%"))
        result = await self.db_session.execute(query)
        return [u for u, in result.scalars().all()]

    async def get_account_by_auth_token(self, auth_token: str) -> Optional[AccountInfo]:
        """Получает аккаунт по токену аутентификации."""
        query = fselect(AccountInfo).where(AccountInfo.auth_token == auth_token)
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()