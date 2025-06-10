# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\monster\ORM_elite_monsters.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Dict, Any, Optional

from game_server.database.models.models import EliteMonster


class EliteMonsterManager:
    """
    CRUD-класс для управления EliteMonster.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_elite_monster(self, data: Dict[str, Any]) -> EliteMonster:
        """
        Создает новую запись элитного монстра в базе данных.
        :param data: Словарь с данными элитного монстра.
        :return: Созданный объект EliteMonster.
        """
        new_monster = EliteMonster(**data)
        self.db_session.add(new_monster)
        self.db_session.commit()
        self.db_session.refresh(new_monster)
        return new_monster

    def get_elite_monster_by_id(self, monster_instance_id: int) -> Optional[EliteMonster]:
        """
        Получает элитного монстра по его ID экземпляра.
        :param monster_instance_id: ID экземпляра элитного монстра.
        :return: Объект EliteMonster или None, если не найден.
        """
        return self.db_session.get(EliteMonster, monster_instance_id)

    def get_all_elite_monsters(self, is_active: Optional[bool] = None) -> List[EliteMonster]:
        """
        Получает всех элитных монстров, опционально фильтруя по статусу активности.
        :param is_active: Если True, возвращает только активных; если False, только неактивных. Если None, всех.
        :return: Список объектов EliteMonster.
        """
        query = select(EliteMonster)
        if is_active is not None:
            query = query.where(EliteMonster.is_active == is_active)
        return self.db_session.scalars(query).all()

    def get_elite_monsters_by_location(self, location: str) -> List[EliteMonster]:
        """
        Получает элитных монстров по их текущей локации.
        :param location: Текущая локация монстра.
        :return: Список объектов EliteMonster.
        """
        return self.db_session.query(EliteMonster).filter_by(current_location=location).all()

    def update_elite_monster(self, monster_instance_id: int, updates: Dict[str, Any]) -> Optional[EliteMonster]:
        """
        Обновляет существующего элитного монстра по его ID экземпляра.
        :param monster_instance_id: ID экземпляра элитного монстра.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект EliteMonster или None, если не найден.
        """
        monster = self.get_elite_monster_by_id(monster_instance_id)
        if monster:
            for key, value in updates.items():
                setattr(monster, key, value)
            self.db_session.commit()
            self.db_session.refresh(monster)
        return monster

    def delete_elite_monster(self, monster_instance_id: int) -> bool:
        """
        Удаляет элитного монстра по его ID экземпляра.
        :param monster_instance_id: ID экземпляра элитного монстра.
        :return: True, если монстр был успешно удален, иначе False.
        """
        monster = self.get_elite_monster_by_id(monster_instance_id)
        if monster:
            self.db_session.delete(monster)
            self.db_session.commit()
            return True
        return False
    
    
    