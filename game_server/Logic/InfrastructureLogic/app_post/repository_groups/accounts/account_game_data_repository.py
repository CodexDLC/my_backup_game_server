# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/account_game_data_repository.py

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from game_server.database.models.models import AccountGameData
from .interfaces_accounts import IAccountGameDataRepository
from game_server.config.logging.logging_setup import app_logger as logger

class AccountGameDataRepositoryImpl(IAccountGameDataRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью AccountGameData.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_account_game_data(self, account_id: int, initial_shard_id: Optional[str] = None) -> Optional[AccountGameData]:
        new_game_data = AccountGameData(
            account_id=account_id,
            shard_id=initial_shard_id,
            last_login_game=datetime.now(timezone.utc),
        )
        self._session.add(new_game_data)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"AccountGameData успешно добавлена в сессию для account_id: {account_id}.")
        return new_game_data

    async def get_account_game_data(self, account_id: int) -> Optional[AccountGameData]:
        stmt = select(AccountGameData).where(AccountGameData.account_id == account_id)
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def update_shard_id(self, account_id: int, new_shard_id: Optional[str]) -> Optional[AccountGameData]:
        stmt = update(AccountGameData).where(AccountGameData.account_id == account_id).values(
            shard_id=new_shard_id
        ).returning(AccountGameData)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Shard ID для аккаунта {account_id} обновлен на '{new_shard_id}' в сессии.")
        return result.scalars().first()

    async def update_last_login_game(self, account_id: int) -> Optional[AccountGameData]:
        stmt = update(AccountGameData).where(AccountGameData.account_id == account_id).values(
            last_login_game=datetime.now(timezone.utc)
        ).returning(AccountGameData)
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"last_login_game для аккаунта {account_id} обновлен в сессии.")
        return result.scalars().first()

    async def get_inactive_accounts_with_shard_id(self, days_inactive: int) -> List[AccountGameData]:
        inactive_threshold = datetime.now(timezone.utc) - timedelta(days=days_inactive)
        stmt = select(AccountGameData).where(
            AccountGameData.last_login_game < inactive_threshold,
            AccountGameData.shard_id.isnot(None)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def clear_shard_id_for_accounts(self, account_ids: List[int]) -> int:
        if not account_ids:
            return 0
        stmt = update(AccountGameData).where(AccountGameData.account_id.in_(account_ids)).values(
            shard_id=None
        )
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Shard ID очищен для {result.rowcount} неактивных аккаунтов в сессии.")
        return result.rowcount

    async def count_players_on_shard(self, shard_id: str) -> int:
        stmt = select(func.count(AccountGameData.account_id)).where(
            AccountGameData.shard_id == shard_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_players_on_all_shards(self) -> Dict[str, int]:
        stmt = select(AccountGameData.shard_id, func.count(AccountGameData.account_id)).where(
            AccountGameData.shard_id.isnot(None)
        ).group_by(AccountGameData.shard_id)
        result = await self._session.execute(stmt)
        return {row.shard_id: row.count for row in result.all()}
