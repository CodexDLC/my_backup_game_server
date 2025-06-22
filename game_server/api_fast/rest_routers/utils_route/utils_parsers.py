from fastapi import Request
from game_server.api_fast.api_models.utils_api import ExportRequest

async def parse_export_request(request: Request) -> ExportRequest:
    """Парсит JSON-запрос на экспорт данных."""
    return ExportRequest(**await request.json())