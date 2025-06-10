# game_server/Logic/InfrastructureLogic/DataAccessLogic/manager/system/item_templates_generator/ORM_suffixes.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import Suffix


class SuffixManager:
    """
    CRUD class for managing Suffix.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_suffix(self, data: Dict[str, Any]) -> Suffix:
        new_suffix = Suffix(**data)
        self.db_session.add(new_suffix)
        self.db_session.commit()
        self.db_session.refresh(new_suffix)
        return new_suffix

    def get_suffix_by_code(self, suffix_code: str) -> Optional[Suffix]:
        return self.db_session.query(Suffix).filter_by(suffix_code=suffix_code).first()

    def get_all_suffixes(self) -> List[Suffix]:
        return self.db_session.query(Suffix).all()
        
    # +++ НОВЫЙ МЕТОД +++
    def get_suffixes_by_group(self, group: str) -> List[Suffix]:
        """
        Retrieves suffixes filtered by group.
        :param group: The group of the suffix (e.g., 'VAMPIRIC', 'ARCANE').
        :return: List of Suffix objects.
        """
        return self.db_session.query(Suffix).filter_by(group=group).all()

    def update_suffix(self, suffix_code: str, updates: Dict[str, Any]) -> Optional[Suffix]:
        suffix = self.get_suffix_by_code(suffix_code)
        if suffix:
            for key, value in updates.items():
                setattr(suffix, key, value)
            self.db_session.commit()
            self.db_session.refresh(suffix)
        return suffix

    def delete_suffix(self, suffix_code: str) -> bool:
        suffix = self.get_suffix_by_code(suffix_code)
        if suffix:
            self.db_session.delete(suffix)
            self.db_session.commit()
            return True
        return False

    def upsert_suffix(self, data: Dict[str, Any]) -> Suffix:
        suffix_code = data.get("suffix_code")
        if not suffix_code:
            raise ValueError("Suffix code must be provided for upsert operation.")

        existing_suffix = self.get_suffix_by_code(suffix_code)
        if existing_suffix:
            for key, value in data.items():
                setattr(existing_suffix, key, value)
            self.db_session.commit()
            self.db_session.refresh(existing_suffix)
            return existing_suffix
        else:
            return self.create_suffix(data)