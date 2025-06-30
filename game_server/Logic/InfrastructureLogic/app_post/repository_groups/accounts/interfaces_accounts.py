# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/accounts/interfaces_accounts.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
# Импорт моделей, используемых в сигнатурах этих интерфейсов
from game_server.database.models.models import AccountGameData, AccountInfo


class IAccountGameDataRepository(ABC):

    @abstractmethod
    async def get_account_game_data(self, account_id: int) -> Optional[AccountGameData]:
        pass
    @abstractmethod
    async def update_shard_id(self, account_id: int, new_shard_id: Optional[str]) -> Optional[AccountGameData]:
        pass
    @abstractmethod
    async def update_last_login_game(self, account_id: int) -> Optional[AccountGameData]:
        pass
    @abstractmethod
    async def get_inactive_accounts_with_shard_id(self, days_inactive: int) -> List[AccountGameData]:
        pass
    @abstractmethod
    async def clear_shard_id_for_accounts(self, account_ids: List[int]) -> int:
        pass
    @abstractmethod
    async def count_players_on_shard(self, shard_id: str) -> int:
        pass
    @abstractmethod
    async def count_players_on_all_shards(self) -> Dict[str, int]:
        pass

class IAccountInfoRepository(ABC):
    @abstractmethod
    async def create_account(self, account_data: Dict[str, Any]) -> AccountInfo: pass
    @abstractmethod
    async def get_account_by_id(self, account_id: int) -> Optional[AccountInfo]: pass
    @abstractmethod
    async def get_account_by_username(self, username: str) -> Optional[AccountInfo]: pass
    @abstractmethod
    async def get_account_by_email(self, email: str) -> Optional[AccountInfo]: pass
    @abstractmethod
    async def get_account_by_identifier(self, identifier_type: str, identifier_value: str) -> Optional[AccountInfo]: pass
    @abstractmethod
    async def update_account(self, account_id: int, update_data: Dict[str, Any]) -> Optional[AccountInfo]: pass
    @abstractmethod
    async def delete_account(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_all_guest_usernames(self) -> List[str]: pass
    @abstractmethod
    async def get_account_by_auth_token(self, auth_token: str) -> Optional[AccountInfo]: pass