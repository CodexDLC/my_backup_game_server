from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.CRUD_LOGIC.CRUD.system.world.crud_world import ManageWorld
from game_server.services.logging.logging_setup import logger
from game_server.database import get_db_session


class SystemGameWorldRoutes:
    router = APIRouter(prefix="/gameworld")

    @router.get("/world", summary="Получить текущий мир")
    async def get_current_world_route(db_session: AsyncSession = Depends(get_db_session)):
        logger.info("Запрос на получение текущего мира")
        result = await ManageWorld.manage_worlds("get", db_session=db_session)
        return SystemGameWorldRoutes.handle_response(result, "Мир не найден")

    @router.get("/regions", response_model=List[str], summary="Получить все регионы для категории в Discord")
    async def get_all_regions_route(db_session: AsyncSession = Depends(get_db_session)):
        logger.info("Запрос на получение всех регионов")
        result = await ManageWorld.manage_regions("get", db_session=db_session)
        return SystemGameWorldRoutes.handle_response(result, "Регионы не найдены", list_key="name")

    @router.get("/subregions/{region_access_key}", response_model=List[str], summary="Получить подрегионы для указанного региона")
    async def get_subregions_route(region_access_key: str, db_session: AsyncSession = Depends(get_db_session)):
        logger.info(f"Запрос на получение подрегионов для region_access_key={region_access_key}")
        result = await ManageWorld.manage_subregions("get", db_session=db_session)
        return SystemGameWorldRoutes.handle_response(result, "Подрегионы не найдены", list_key="name", filter_key="access_key", filter_value=region_access_key)

    @staticmethod
    def handle_response(result, error_message, list_key=None, filter_key=None, filter_value=None):
        """Обрабатывает ответ CRUD-функций и упрощает роута-код."""
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=error_message)
        
        data = result["data"]
        if list_key:
            data = [row[list_key] for row in data]
        if filter_key and filter_value:
            data = [row[list_key] for row in data if row[filter_key] == filter_value]
        
        return data
