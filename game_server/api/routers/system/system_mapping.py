from fastapi import APIRouter, HTTPException
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from pydantic import BaseModel
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import EntityStateMap  # Импортируем модель EntityStateMap


# -------------------- Модели --------------------
class MappingResponse(BaseModel):
    entity_access_key: str
    access_code: int

class EntityStateMapRequest(BaseModel):
    entity_access_key: str
    access_code: int


# -------------------- Роуты --------------------
router = APIRouter()

@router.get("/entity-state/map", response_model=List[MappingResponse], summary="Получить все связи entity_access_key ↔ access_code")
async def get_entity_state_map():
    logger.info("Запрос на получение карты сущностей (entity_access_key ↔ access_code)")
    
    try:
        async with get_db_session() as session:
            query = select(EntityStateMap.entity_access_key, EntityStateMap.access_code)
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="Связи не найдены")
            
            return [MappingResponse(entity_access_key=row.entity_access_key, access_code=row.access_code) for row in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при получении карты сущностей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении карты сущностей")


@router.post("/entity-state/map", summary="Добавить новую связь entity_access_key ↔ access_code в глобальный шаблон")
async def add_entity_state_map(payload: EntityStateMapRequest):
    logger.info(f"Добавление новой связи: entity_access_key={payload.entity_access_key}, access_code={payload.access_code}")
    
    try:
        async with get_db_session() as session:
            new_mapping = EntityStateMap(
                entity_access_key=payload.entity_access_key,
                access_code=payload.access_code
            )
            session.add(new_mapping)
            await session.commit()  # Сохраняем изменения в базе данных
            
            logger.info(f"INFO Связь между entity_access_key={payload.entity_access_key} и access_code={payload.access_code} успешно добавлена")
            return {"status": "Связь добавлена"}
    
    except Exception as e:
        logger.error(f"Ошибка при добавлении связи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении связи")


@router.get("/entity-state/map/{entity_access_key}", response_model=List[int], summary="Получить список access_code для указанного entity_access_key")
async def get_entity_access_code(entity_access_key: str):
    logger.info(f"Запрос на получение списка access_code для entity_access_key={entity_access_key}")
    
    try:
        async with get_db_session() as session:
            query = select(EntityStateMap.access_code).where(EntityStateMap.entity_access_key == entity_access_key)
            result = await session.execute(query)
            rows = result.fetchall()
            
            if not rows:
                raise HTTPException(status_code=404, detail="access_code не найдены для указанного entity_access_key")
            
            return [row.access_code for row in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при получении access_code: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении access_code")


@router.delete("/entity-state/map/{entity_access_key}/{access_code}", summary="Удалить связь между entity_access_key и access_code")
async def delete_entity_state_map(entity_access_key: str, access_code: int):
    logger.info(f"Удаление связи для entity_access_key={entity_access_key}, access_code={access_code}")
    
    try:
        async with get_db_session() as session:
            query = select(EntityStateMap).where(
                EntityStateMap.entity_access_key == entity_access_key,
                EntityStateMap.access_code == access_code
            )
            result = await session.execute(query)
            mapping = result.scalar_one_or_none()
            
            if not mapping:
                raise HTTPException(status_code=404, detail="Связь не найдена")
            
            await session.delete(mapping)  # Удаляем найденную запись
            await session.commit()  # Сохраняем изменения
            
            logger.info(f"INFO Связь между entity_access_key={entity_access_key} и access_code={access_code} успешно удалена")
            return {"status": "Связь удалена"}
    
    except Exception as e:
        logger.error(f"Ошибка при удалении связи: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении связи")
