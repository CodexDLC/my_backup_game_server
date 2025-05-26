from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.CRUD_LOGIC.CRUD.system.world.crud_state_entities import manage_entity_state_map
from game_server.Logic.DataAccessLogic.db_instance import get_db_session

class EntityStateMapPayload(BaseModel):
    """Модель для валидации входных данных POST-запроса"""
    entity_access_key: str
    access_code: int

class EntityStateRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/entity-state", tags=["Entity State Management"])
        self._setup_routes()

    def _setup_routes(self):
        @self.router.get(
            "/map", 
            summary="Получить все связи entity_access_key ↔ access_code",
            response_description="Словарь всех связей"
        )
        async def get_all_mappings(db_session: AsyncSession = Depends(get_db_session)):
            return await manage_entity_state_map("get", db_session=db_session)

        @self.router.post(
            "/map",
            summary="Добавить новую связь entity_access_key ↔ access_code",
            status_code=status.HTTP_201_CREATED,
            response_description="Созданная связь"
        )
        async def add_mapping(
            payload: EntityStateMapPayload, 
            db_session: AsyncSession = Depends(get_db_session)
        ):
            return await manage_entity_state_map(
                "insert",
                entity_access_key=payload.entity_access_key,
                state_data={"access_code": payload.access_code},
                db_session=db_session
            )

        @self.router.get(
            "/map/{entity_access_key}",
            summary="Получить список access_code для указанного entity_access_key",
            responses={404: {"description": "Связь не найдена"}}
        )
        async def get_mapping(
            entity_access_key: str, 
            db_session: AsyncSession = Depends(get_db_session)
        ):
            result = await manage_entity_state_map(
                "get", 
                entity_access_key=entity_access_key, 
                db_session=db_session
            )
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Связь не найдена"
                )
            return result

        @self.router.delete(
            "/map/{entity_access_key}/{access_code}",
            summary="Удалить связь между entity_access_key и access_code",
            status_code=status.HTTP_204_NO_CONTENT,
            responses={
                404: {"description": "Связь не найдена"},
                204: {"description": "Связь успешно удалена"}
            }
        )
        async def delete_mapping(
            entity_access_key: str, 
            access_code: int, 
            db_session: AsyncSession = Depends(get_db_session)
        ):
            success = await manage_entity_state_map(
                "delete",
                entity_access_key=entity_access_key,
                state_data={"access_code": access_code},
                db_session=db_session
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Связь не найдена"
                )