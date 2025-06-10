# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\system\iten_templates_generator\ORM_materials.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import Material


class MaterialManager:
    """
    CRUD-класс для управления Material.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_material(self, data: Dict[str, Any]) -> Material:
        """
        Создает новую запись материала в базе данных.
        :param data: Словарь с данными материала.
        :return: Созданный объект Material.
        """
        new_material = Material(**data)
        self.db_session.add(new_material)
        self.db_session.commit()
        self.db_session.refresh(new_material)
        return new_material

    def get_material_by_code(self, material_code: str) -> Optional[Material]:
        """
        Получает материал по его коду.
        :param material_code: Код материала.
        :return: Объект Material или None, если не найден.
        """
        return self.db_session.query(Material).filter_by(material_code=material_code).first()

    def get_all_materials(self) -> List[Material]:
        """
        Получает все материалы из базы данных.
        :return: Список объектов Material.
        """
        return self.db_session.query(Material).all()

    def update_material(self, material_code: str, updates: Dict[str, Any]) -> Optional[Material]:
        """
        Обновляет существующий материал по его коду.
        :param material_code: Код материала.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект Material или None, если не найден.
        """
        material = self.get_material_by_code(material_code)
        if material:
            for key, value in updates.items():
                setattr(material, key, value)
            self.db_session.commit()
            self.db_session.refresh(material)
        return material

    def delete_material(self, material_code: str) -> bool:
        """
        Удаляет материал по его коду.
        :param material_code: Код материала.
        :return: True, если материал был успешно удален, иначе False.
        """
        material = self.get_material_by_code(material_code)
        if material:
            self.db_session.delete(material)
            self.db_session.commit()
            return True
        return False

    def upsert_material(self, data: Dict[str, Any]) -> Material:
        """
        Создает или обновляет материал. Если материал с данным material_code существует,
        он обновляется; иначе создается новый.
        :param data: Словарь с данными материала. material_code должен быть предоставлен.
        :return: Созданный или обновленный объект Material.
        """
        material_code = data.get("material_code")
        if not material_code:
            raise ValueError("Material code must be provided for upsert operation.")

        existing_material = self.get_material_by_code(material_code)
        if existing_material:
            for key, value in data.items():
                setattr(existing_material, key, value)
            self.db_session.commit()
            self.db_session.refresh(existing_material)
            return existing_material
        else:
            return self.create_material(data)