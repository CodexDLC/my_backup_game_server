# game_server/database/crud/item_base_crud.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import ItemBase


class ItemBaseManager:
    """
    CRUD-класс для управления ItemBase.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_item_base(self, data: Dict[str, Any]) -> ItemBase:
        """
        Создает новую запись базового архетипа предмета в базе данных.
        :param data: Словарь с данными архетипа (base_item_code, category, properties_json).
        :return: Созданный объект ItemBase.
        """
        new_item_base = ItemBase(**data)
        self.db_session.add(new_item_base)
        self.db_session.commit()
        self.db_session.refresh(new_item_base)
        return new_item_base

    def get_item_base_by_code(self, base_item_code: str) -> Optional[ItemBase]:
        """
        Получает базовый архетип предмета по его коду.
        :param base_item_code: Код архетипа.
        :return: Объект ItemBase или None, если не найден.
        """
        return self.db_session.query(ItemBase).filter_by(base_item_code=base_item_code).first()

    def get_all_item_bases(self) -> List[ItemBase]:
        """
        Получает все базовые архетипы предметов.
        :return: Список объектов ItemBase.
        """
        return self.db_session.query(ItemBase).all()

    def get_item_bases_by_category(self, category: str) -> List[ItemBase]:
        """
        Получает базовые архетипы предметов по категории.
        :param category: Категория предмета (например, 'WEAPON', 'ARMOR').
        :return: Список объектов ItemBase.
        """
        return self.db_session.query(ItemBase).filter_by(category=category).all()

    def update_item_base(self, base_item_code: str, updates: Dict[str, Any]) -> Optional[ItemBase]:
        """
        Обновляет существующий базовый архетип предмета по его коду.
        :param base_item_code: Код архетипа.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект ItemBase или None, если не найден.
        """
        item_base = self.get_item_base_by_code(base_item_code)
        if item_base:
            for key, value in updates.items():
                setattr(item_base, key, value)
            self.db_session.commit()
            self.db_session.refresh(item_base)
        return item_base

    def delete_item_base(self, base_item_code: str) -> bool:
        """
        Удаляет базовый архетип предмета по его коду.
        :param base_item_code: Код архетипа.
        :return: True, если архетип был успешно удален, иначе False.
        """
        item_base = self.get_item_base_by_code(base_item_code)
        if item_base:
            self.db_session.delete(item_base)
            self.db_session.commit()
            return True
        return False

    def upsert_item_base(self, data: Dict[str, Any]) -> ItemBase:
        """
        Создает или обновляет базовый архетип предмета. Если архетип с данным base_item_code существует,
        он обновляется; иначе создается новый.
        :param data: Словарь с данными архетипа. base_item_code должен быть предоставлен.
        :return: Созданный или обновленный объект ItemBase.
        """
        base_item_code = data.get("base_item_code")
        if not base_item_code:
            raise ValueError("Base item code must be provided for upsert operation.")

        existing_item_base = self.get_item_base_by_code(base_item_code)
        if existing_item_base:
            for key, value in data.items():
                setattr(existing_item_base, key, value)
            self.db_session.commit()
            self.db_session.refresh(existing_item_base)
            return existing_item_base
        else:
            return self.create_item_base(data)