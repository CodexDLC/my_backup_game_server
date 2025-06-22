# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/account_game_data_repository.py

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.exc import IntegrityError, NoResultFound

# Импорт вашей модели AccountGameData
from game_server.database.models.models import AccountGameData 

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository 

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class AccountGameDataRepositoryImpl(IAccountGameDataRepository): # <-- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для выполнения CRUD-операций с моделью AccountGameData.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    """
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_account_game_data(self, account_id: int) -> Optional[AccountGameData]:
        """
        Получает игровые данные аккаунта по account_id.
        """
        stmt = select(AccountGameData).where(AccountGameData.account_id == account_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().first()

    async def update_shard_id(self, account_id: int, new_shard_id: Optional[str]) -> Optional[AccountGameData]:
        """
        Обновляет shard_id для аккаунта.
        Установка new_shard_id в None/NULL отключает аккаунт от шарда.
        """
        stmt = update(AccountGameData).where(AccountGameData.account_id == account_id).values(
            shard_id=new_shard_id
        ).returning(AccountGameData)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        logger.info(f"Shard ID для аккаунта {account_id} обновлен на '{new_shard_id}'.")
        return result.scalars().first()

    async def update_last_login_game(self, account_id: int) -> Optional[AccountGameData]:
        """
        Обновляет last_login_game для аккаунта до текущего времени.
        Это поле используется для отслеживания общей активности аккаунта.
        """
        stmt = update(AccountGameData).where(AccountGameData.account_id == account_id).values(
            last_login_game=func.now() # Используем func.now() для получения текущего времени БД
        ).returning(AccountGameData)
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        logger.info(f"last_login_game для аккаунта {account_id} обновлен.")
        return result.scalars().first()

    async def get_inactive_accounts_with_shard_id(self, days_inactive: int) -> List[AccountGameData]:
        """
        Получает список неактивных аккаунтов, которые все еще привязаны к шарду.
        Неактивность определяется по last_login_game.
        """
        inactive_threshold = datetime.now() - timedelta(days=days_inactive)
        stmt = select(AccountGameData).where(
            AccountGameData.last_login_game < inactive_threshold, 
            AccountGameData.shard_id.isnot(None) # Только те, у кого есть привязка к шарду
        )
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

    async def clear_shard_id_for_accounts(self, account_ids: List[int]) -> int:
        """
        Очищает shard_id для списка аккаунтов.
        Возвращает количество обновленных записей.
        """
        if not account_ids:
            return 0
        stmt = update(AccountGameData).where(AccountGameData.account_id.in_(account_ids)).values(
            shard_id=None # Устанавливаем в NULL
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        logger.info(f"Shard ID очищен для {result.rowcount} неактивных аккаунтов.")
        return result.rowcount

    async def count_players_on_shard(self, shard_id: str) -> int:
        """
        Считает количество игроков на конкретном шарде.
        Используется для ежесуточной синхронизации.
        """
        stmt = select(func.count(AccountGameData.account_id)).where(
            AccountGameData.shard_id == shard_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one()

    async def count_players_on_all_shards(self) -> Dict[str, int]:
        """
        Считает количество игроков на всех шардах, возвращая словарь {shard_id: count}.
        Используется для ежесуточной синхронизации всех шардов.
        """
        stmt = select(AccountGameData.shard_id, func.count(AccountGameData.account_id)).where(
            AccountGameData.shard_id.isnot(None)
        ).group_by(AccountGameData.shard_id)
        result = await self.db_session.execute(stmt)
        return {row.shard_id: row.count for row in result.all()}