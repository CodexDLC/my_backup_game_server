# game_server\common_contracts\api_models\utils_api.py

# BaseModel и Field теперь импортируем из shared_models.api_contracts


from pydantic import BaseModel, Field
from game_server.common_contracts.shared_models.api_contracts import BaseRequest


class ExportRequest(BaseRequest): # Наследуем от BaseRequest
    schema_name: str = Field(..., description="Имя схемы (таблицы) для экспорта.")

class ExportData(BaseModel):
    status: str
    folder: str