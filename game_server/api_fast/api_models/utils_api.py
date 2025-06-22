# api_models/utils_api.py
from pydantic import BaseModel, Field

class ExportRequest(BaseModel):
    schema_name: str = Field(..., description="Имя схемы (таблицы) для экспорта.")

class ExportData(BaseModel):
    status: str
    folder: str