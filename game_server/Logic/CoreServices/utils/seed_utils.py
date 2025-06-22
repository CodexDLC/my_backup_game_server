# -*- coding: utf-8 -*-
from sqlalchemy import inspect
from game_server.config.constants.seeds import MODEL_PK_OVERRIDES
from game_server.database.models.models import Base


def get_pk_column_name(model: Base) -> str:
    """
    Получает имя колонки первичного ключа для модели SQLAlchemy.
    Сначала проверяет словарь переопределений, затем использует inspector.
    """
    model_name = model.__name__
    # Используем константу MODEL_PK_OVERRIDES
    if model_name in MODEL_PK_OVERRIDES:
        return MODEL_PK_OVERRIDES[model_name]

    inspector = inspect(model)
    if not inspector.primary_key:
        raise RuntimeError(f"Не удалось определить PK для модели {model_name} через inspector.")

    return inspector.primary_key[0].name