# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\system\iten_templates_generator\ORM_instanced_items.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import InstancedItem


class InstancedItemManager:
    """
    CRUD-класс для управления InstancedItem.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_item_instance(self, data: Dict[str, Any]) -> InstancedItem:
        """
        Создает новую запись экземпляра предмета в базе данных.
        :param data: Словарь с данными экземпляра.
        :return: Созданный объект InstancedItem.
        """
        new_instance = InstancedItem(**data)
        self.db_session.add(new_instance)
        self.db_session.commit()
        self.db_session.refresh(new_instance)
        return new_instance

    def get_item_instance_by_id(self, instance_id: int) -> Optional[InstancedItem]:
        """
        Получает экземпляр предмета по его ID.
        :param instance_id: ID экземпляра предмета.
        :return: Объект InstancedItem или None, если не найден.
        """
        return self.db_session.query(InstancedItem).filter_by(instance_id=instance_id).first()

    def get_items_by_owner(self, owner_id: int, owner_type: str, location_type: Optional[str] = None) -> List[InstancedItem]:
        """
        Получает все экземпляры предметов, принадлежащие определенному владельцу,
        опционально фильтруя по типу местоположения.
        :param owner_id: ID владельца.
        :param owner_type: Тип владельца ('CHARACTER', 'MONSTER' и т.д.).
        :param location_type: Тип местоположения (например, 'INVENTORY', 'EQUIPPED'). Если None, возвращает все.
        :return: Список объектов InstancedItem.
        """
        query = self.db_session.query(InstancedItem).filter_by(owner_id=owner_id, owner_type=owner_type)
        if location_type:
            query = query.filter_by(location_type=location_type)
        return query.all()

    def update_item_instance(self, instance_id: int, updates: Dict[str, Any]) -> Optional[InstancedItem]:
        """
        Обновляет существующий экземпляр предмета по его ID.
        :param instance_id: ID экземпляра предмета.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект InstancedItem или None, если не найден.
        """
        item_instance = self.get_item_instance_by_id(instance_id)
        if item_instance:
            for key, value in updates.items():
                setattr(item_instance, key, value)
            self.db_session.commit()
            self.db_session.refresh(item_instance)
        return item_instance

    def delete_item_instance(self, instance_id: int) -> bool:
        """
        Удаляет экземпляр предмета по его ID.
        :param instance_id: ID экземпляра предмета.
        :return: True, если экземпляр был успешно удален, иначе False.
        """
        item_instance = self.get_item_instance_by_id(instance_id)
        if item_instance:
            self.db_session.delete(item_instance)
            self.db_session.commit()
            return True
        return False

    def transfer_item_instance(self, instance_id: int, new_owner_id: int, new_owner_type: str, new_location_type: str, new_location_slot: Optional[str] = None) -> Optional[InstancedItem]:
        """
        Перемещает экземпляр предмета к новому владельцу или в новое местоположение.
        :param instance_id: ID экземпляра предмета.
        :param new_owner_id: ID нового владельца.
        :param new_owner_type: Тип нового владельца.
        :param new_location_type: Новый тип местоположения.
        :param new_location_slot: Новый слот местоположения (опционально).
        :return: Обновленный объект InstancedItem или None, если не найден.
        """
        item_instance = self.get_item_instance_by_id(instance_id)
        if item_instance:
            item_instance.owner_id = new_owner_id
            item_instance.owner_type = new_owner_type
            item_instance.location_type = new_location_type
            item_instance.location_slot = new_location_slot
            self.db_session.commit()
            self.db_session.refresh(item_instance)
        return item_instance