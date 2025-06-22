# rest_routers/utils_route/import_yami.py
from fastapi import APIRouter, Depends
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response
from game_server.api_fast.api_models.utils_api import ExportRequest, ExportData
from game_server.api_fast.dependencies import get_export_service # <-- Новая зависимость
from .utils_parsers import parse_export_request
from game_server.Logic.DomainLogic.utils.export_service import ExportService, ExportError

router = APIRouter()

@router.post("/export", response_model=APIResponse[ExportData])
async def export_data_route(
    request_data: ExportRequest = Depends(parse_export_request),
    export_service: ExportService = Depends(get_export_service)
):
    """Вызывает скрипт экспорта данных в YAML по указанной схеме."""
    try:
        result_folder = await export_service.export_schema_to_yaml(request_data.schema_name)
        response_data = ExportData(
            status=f"Экспорт для схемы '{request_data.schema_name}' успешно завершён!",
            folder=result_folder
        )
        return create_success_response(data=response_data)
    except ExportError as e:
        return create_error_response(code="EXPORT_FAILED", message=str(e))
    except Exception as e:
        return create_error_response(code="INTERNAL_SERVER_ERROR", message=f"Непредвиденная ошибка экспорта: {e}")

import_yami_route = router