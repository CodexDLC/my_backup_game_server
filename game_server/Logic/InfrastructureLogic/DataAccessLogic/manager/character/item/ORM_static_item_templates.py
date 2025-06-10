# game_server\Logic\InfrastructureLogic\DataAccessLogic\manager\system\iten_templates_generator\ORM_static_item_templates.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from game_server.database.models.models import StaticItemTemplate


class StaticItemTemplateManager:
    """
    CRUD-класс для управления StaticItemTemplate.
    """
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_template(self, data: Dict[str, Any]) -> StaticItemTemplate:
        """
        Создает новый шаблон статического предмета.
        :param data: Словарь с данными шаблона.
        :return: Созданный объект StaticItemTemplate.
        """
        new_template = StaticItemTemplate(**data)
        self.db_session.add(new_template)
        self.db_session.commit()
        self.db_session.refresh(new_template)
        return new_template

    def get_template_by_id(self, template_id: int) -> Optional[StaticItemTemplate]:
        """
        Получает шаблон по его ID.
        :param template_id: ID шаблона.
        :return: Объект StaticItemTemplate или None, если не найден.
        """
        return self.db_session.query(StaticItemTemplate).filter_by(template_id=template_id).first()

    def get_template_by_code(self, item_code: str) -> Optional[StaticItemTemplate]:
        """
        Получает шаблон по его item_code.
        :param item_code: Код статического предмета.
        :return: Объект StaticItemTemplate или None, если не найден.
        """
        return self.db_session.query(StaticItemTemplate).filter_by(item_code=item_code).first()

    def get_all_templates(self) -> List[StaticItemTemplate]:
        """
        Получает все шаблоны статических предметов.
        :return: Список объектов StaticItemTemplate.
        """
        return self.db_session.query(StaticItemTemplate).all()

    def update_template(self, template_id: int, updates: Dict[str, Any]) -> Optional[StaticItemTemplate]:
        """
        Обновляет существующий шаблон по его ID.
        :param template_id: ID шаблона.
        :param updates: Словарь с полями для обновления.
        :return: Обновленный объект StaticItemTemplate или None, если не найден.
        """
        template = self.get_template_by_id(template_id)
        if template:
            for key, value in updates.items():
                setattr(template, key, value)
            self.db_session.commit()
            self.db_session.refresh(template)
        return template

    def delete_template(self, template_id: int) -> bool:
        """
        Удаляет шаблон по его ID.
        :param template_id: ID шаблона.
        :return: True, если шаблон был успешно удален, иначе False.
        """
        template = self.get_template_by_id(template_id)
        if template:
            self.db_session.delete(template)
            self.db_session.commit()
            return True
        return False

    def upsert_template(self, data: Dict[str, Any]) -> StaticItemTemplate:
        """
        Создает или обновляет шаблон. Если шаблон с данным item_code существует,
        он обновляется; иначе создается новый.
        :param data: Словарь с данными шаблона. item_code должен быть предоставлен.
        :return: Созданный или обновленный объект StaticItemTemplate.
        """
        item_code = data.get("item_code")
        if not item_code:
            raise ValueError("Item code must be provided for upsert operation.")

        existing_template = self.get_template_by_code(item_code)
        if existing_template:
            for key, value in data.items():
                setattr(existing_template, key, value)
            self.db_session.commit()
            self.db_session.refresh(existing_template)
            return existing_template
        else:
            return self.create_template(data)