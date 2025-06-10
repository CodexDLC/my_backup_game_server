from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from game_server.Logic.InterfacesLogic.system_route_logic.system_gameworld_logic import SystemGameWorldLogic
from game_server.services.logging.logging_setup import logger


router = APIRouter()

@router.get("/world", summary="Получить текущий мир")
async def get_current_world_route(db_session: AsyncSession = Depends(get_db_session)):
    logger.info("Запрос на получение текущего мира")
    result = await SystemGameWorldLogic.get_current_world(db_session)  # Передаём сессию
    return SystemGameWorldLogic.handle_response(result, "Мир не найден")

@router.get("/regions", response_model=list, summary="Получить все регионы")
async def get_all_regions_route(db_session: AsyncSession = Depends(get_db_session)):
    logger.info("Запрос на получение всех регионов")
    result = await SystemGameWorldLogic.get_all_regions(db_session)  # Передаём сессию
    return SystemGameWorldLogic.handle_response(result, "Регионы не найдены")  # Убрали list_key


@router.get("/subregions", response_model=list, summary="Получить все подрегионы")
async def get_all_subregions_route(db_session: AsyncSession = Depends(get_db_session)):
    logger.info("Запрос на получение всех подрегионов")

    result = await SystemGameWorldLogic.get_all_subregions(db_session)

    return SystemGameWorldLogic.handle_response(result, "Подрегионы не найдены")




system_gameworld_router = router
