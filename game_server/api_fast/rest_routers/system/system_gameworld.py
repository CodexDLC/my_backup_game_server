# game_server/api_fast/rest_routers/system/system_gameworld.py

from fastapi import APIRouter, Depends
from typing import List, Dict, Any # Добавлен Dict, Any для аннотаций ожидаемых словарей
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response

from game_server.api_fast.api_models.system_api import RegionData, WorldData, SubregionData # <--- ДОБАВЛЕН SubregionData
from game_server.api_fast.dependencies import get_gameworld_service
from game_server.Logic.PresentationLayer.system_route_logic.system_gameworld_logic import SystemGameWorldLogic, WorldDataNotFoundException
router = APIRouter()

# Импортируем настроенный глобальный логгер сервера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger 
logger = server_logger.getChild(__name__)


@router.get("/world", response_model=APIResponse[WorldData])
async def get_current_world_route(gameworld_service: SystemGameWorldLogic = Depends(get_gameworld_service)):
    logger.info("Получен запрос: GET /system/gameworld/world")
    try:
        # Бизнес-логика предположительно возвращает словарь или ORM-объект
        world_data_from_logic: Dict[str, Any] = await gameworld_service.get_current_world()
        
        # Преобразуем данные из логики в Pydantic-модель для ответа API
        world_response_model = WorldData.model_validate(world_data_from_logic) # Используем model_validate для гибкости
        
        return create_success_response(data=world_response_model, message="Данные текущего мира успешно получены.")
    except WorldDataNotFoundException as e:
        logger.warning(f"Данные мира не найдены: {e}")
        return create_error_response(code="NOT_FOUND", message=str(e))
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении данных мира: {e}", exc_info=True)
        return create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error")

@router.get("/regions", response_model=APIResponse[List[RegionData]])
async def get_all_regions_route(gameworld_service: SystemGameWorldLogic = Depends(get_gameworld_service)):
    logger.info("Получен запрос: GET /system/gameworld/regions")
    try:
        # Бизнес-логика предположительно возвращает список словарей или ORM-объектов
        regions_data_from_logic: List[Dict[str, Any]] = await gameworld_service.get_all_regions()
        
        # Преобразуем данные из логики в список Pydantic-моделей для ответа API
        regions_response_models = [RegionData.model_validate(region) for region in regions_data_from_logic]
        
        return create_success_response(data=regions_response_models, message="Список регионов успешно получен.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении списка регионов: {e}", exc_info=True)
        return create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error")

# --- НОВЫЙ РОУТ ДЛЯ SUBREGIONS ---
@router.get("/subregions", response_model=APIResponse[List[SubregionData]]) # <--- НОВЫЙ РОУТ
async def get_all_subregions_route(gameworld_service: SystemGameWorldLogic = Depends(get_gameworld_service)):
    logger.info("Получен запрос: GET /system/gameworld/subregions")
    try:
        # Бизнес-логика предположительно возвращает список словарей или ORM-объектов
        subregions_data_from_logic: List[Dict[str, Any]] = await gameworld_service.get_all_subregions() # <--- Предполагаем, что этот метод будет в SystemGameWorldLogic
        
        # Преобразуем данные из логики в список Pydantic-моделей для ответа API
        subregions_response_models = [SubregionData.model_validate(subregion) for subregion in subregions_data_from_logic]
        
        return create_success_response(data=subregions_response_models, message="Список субрегионов успешно получен.")
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при получении списка субрегионов: {e}", exc_info=True)
        return create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error")


system_gameworld_router = router
