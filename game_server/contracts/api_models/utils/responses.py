# contracts/api_models/utils/responses.py

from pydantic import BaseModel, Field

class ExportData(BaseModel):
    """
    Модель данных для ответа об экспорте.
    Перенесено из game_server/common_contracts/api_models/utils_api.py
    """
    status: str
    folder: str

