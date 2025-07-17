# contracts/api_models/utils/requests.py

from pydantic import Field

from game_server.contracts.shared_models.base_requests import BaseRequest



class ExportRequest(BaseRequest):
    """
    Модель запроса для экспорта данных.
    Перенесено из game_server/common_contracts/api_models/utils_api.py
    """
    schema_name: str = Field(..., description="Имя схемы (таблицы) для экспорта.")

