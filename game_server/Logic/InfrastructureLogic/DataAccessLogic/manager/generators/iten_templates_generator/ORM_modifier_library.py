# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\system\iten_templates_generator\ORM_modifier_library.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import ModifierLibrary


class ModifierLibraryManager:
    """
    CRUD-класс для управления ModifierLibrary.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_modifier(self, data: Dict[str, Any]) -> ModifierLibrary:
        """
        Создает новую запись модификатора в базе данных.
        :param data: Словарь с данными модификатора (modifier_code, name, effect_description, value_tiers, randomization_range).
        :return: Созданный объект ModifierLibrary.
        """
        new_modifier = ModifierLibrary(**data)
        self.db_session.add(new_modifier)
        self.db_session.commit()
        self.db_session.refresh(new_modifier)
        return new_modifier

    def get_modifier_by_code(self, modifier_code: str) -> Optional[ModifierLibrary]:
        """
        Получает модификатор по его коду.
        :param modifier_code: Код модификатора.
        :return: Объект ModifierLibrary или None, если не найден.
        """
        return self.db_session.query(ModifierLibrary).filter_by(modifier_code=modifier_code).first()

    def get_all_modifiers(self) -> List[ModifierLibrary]:
        """
        Получает все модификаторы из базы данных.
        :return: Список объектов ModifierLibrary.
        """
        return self.db_session.query(ModifierLibrary).all()

    def update_modifier(self, modifier_code: str, updates: Dict[str, Any]) -> Optional[ModifierLibrary]:
        """
        Обновляет существующий модификатор по его коду.
        :param modifier_code: Код модификатора.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект ModifierLibrary или None, если не найден.
        """
        modifier = self.get_modifier_by_code(modifier_code)
        if modifier:
            for key, value in updates.items():
                setattr(modifier, key, value)
            self.db_session.commit()
            self.db_session.refresh(modifier)
        return modifier

    def delete_modifier(self, modifier_code: str) -> bool:
        """
        Удаляет модификатор по его коду.
        :param modifier_code: Код модификатора.
        :return: True, если модификатор был успешно удален, иначе False.
        """
        modifier = self.get_modifier_by_code(modifier_code)
        if modifier:
            self.db_session.delete(modifier)
            self.db_session.commit()
            return True
        return False

    def upsert_modifier(self, data: Dict[str, Any]) -> ModifierLibrary:
        """
        Создает или обновляет модификатор. Если модификатор с данным modifier_code существует,
        он обновляется; иначе создается новый.
        :param data: Словарь с данными модификатора.
        :return: Созданный или обновленный объект ModifierLibrary.
        """
        modifier_code = data.get("modifier_code")
        if not modifier_code:
            raise ValueError("Modifier code must be provided for upsert operation.")

        existing_modifier = self.get_modifier_by_code(modifier_code)
        if existing_modifier:
            for key, value in data.items():
                setattr(existing_modifier, key, value)
            self.db_session.commit()
            self.db_session.refresh(existing_modifier)
            return existing_modifier
        else:
            return self.create_modifier(data)