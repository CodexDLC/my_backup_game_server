from pathlib import Path
from typing import Dict
from sqlalchemy import inspect

class SeedsConfig:
    SEEDS_DIR = Path("game_server/database/seeds")
    BATCH_SIZE = 50
    MODEL_PK_OVERRIDES: Dict[str, str] = {
        'QuestSteps': 'step_key'  # Используем step_key как идентификатор
    }
    
    @classmethod
    def get_pk_column(cls, model) -> str:
        """Получаем имя PK колонки с учетом переопределений"""
        model_name = model.__name__
        if model_name in cls.MODEL_PK_OVERRIDES:
            return cls.MODEL_PK_OVERRIDES[model_name]
        
        inspector = inspect(model)
        return inspector.primary_key[0].name