from fastapi import APIRouter, HTTPException, Depends
from game_server.database.models.models import AppliedPermissions
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session  # Импортируем сессию SQLAlchemy
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# -------------------- Модель запроса --------------------
class AppliedPermissionResponse(BaseModel):
    entity_access_key: str
    access_code: int
    target_type: str
    target_id: int
    role_id: int
    applied_at: str

class AppliedPermissionRequest(BaseModel):
    entity_access_key: str
    access_code: int
    target_type: str
    target_id: int
    role_id: int


# -------------------- GET /applied-permissions --------------------
@router.get("/applied-permissions", response_model=List[AppliedPermissionResponse], summary="Получить все примененные права для указанной гильдии")
async def get_applied_permissions(guild_id: int, db: AsyncSession = Depends(get_db_session)):  # Подключаем сессию SQLAlchemy
    logger.info(f"Запрос на получение примененных прав для guild_id={guild_id}")
    
    try:
        # Выполнение запроса через SQLAlchemy
        stmt = select(AppliedPermissions).filter_by(guild_id=guild_id)
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.info(f"⚠️ Примененные права для guild_id={guild_id} не найдены")
            return []
        
        return [AppliedPermissionResponse(**dict(r)) for r in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при получении примененных прав: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении примененных прав")


# -------------------- POST /applied-permissions --------------------
@router.post("/applied-permissions", summary="Регистрация факта применения прав")
async def apply_permissions(guild_id: int, payload: AppliedPermissionRequest, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Регистрация факта применения прав для guild_id={guild_id}, entity_access_key={payload.entity_access_key}")
    
    try:
        # Выполняем вставку через SQLAlchemy
        new_permission = AppliedPermissions(
            guild_id=guild_id,
            entity_access_key=payload.entity_access_key,
            access_code=payload.access_code,
            target_type=payload.target_type,
            target_id=payload.target_id,
            role_id=payload.role_id,
            applied_at=datetime.utcnow()
        )
        db.add(new_permission)
        await db.commit()

        logger.info(f"INFO Факт применения прав зарегистрирован для guild_id={guild_id}")
        return {"status": "Факт применения прав сохранен"}
    
    except Exception as e:
        logger.error(f"Ошибка при регистрации факта применения прав: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при регистрации факта применения прав")


# -------------------- GET /applied-permissions/{entity_access_key}/{access_code} --------------------
@router.get("/applied-permissions/{entity_access_key}/{access_code}", response_model=List[AppliedPermissionResponse], summary="Проверить, были ли применены права для пары")
async def check_applied_permissions(entity_access_key: str, access_code: int, guild_id: int, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Проверка применения прав для entity_access_key={entity_access_key}, access_code={access_code}, guild_id={guild_id}")
    
    try:
        # Выполняем запрос через SQLAlchemy
        stmt = select(AppliedPermissions).filter_by(entity_access_key=entity_access_key, access_code=access_code, guild_id=guild_id)
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.info(f"⚠️ Для указанной пары (entity_access_key={entity_access_key}, access_code={access_code}) в guild_id={guild_id} не найдено примененных прав")
            return []
        
        return [AppliedPermissionResponse(**dict(r)) for r in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при проверке примененных прав: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при проверке примененных прав")


# -------------------- DELETE /applied-permissions/{entity_access_key}/{access_code}/{target_type}/{target_id}/{role_id} --------------------
@router.delete("/applied-permissions/{entity_access_key}/{access_code}/{target_type}/{target_id}/{role_id}", summary="Удалить запись о примененных правах")
async def delete_applied_permissions(entity_access_key: str, access_code: int, target_type: str, target_id: int, role_id: int, guild_id: int, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Удаление записи о примененных правах для entity_access_key={entity_access_key}, access_code={access_code}, target_type={target_type}, target_id={target_id}, role_id={role_id}, guild_id={guild_id}")
    
    try:
        stmt = select(AppliedPermissions).filter_by(
            entity_access_key=entity_access_key,
            access_code=access_code,
            target_type=target_type,
            target_id=target_id,
            role_id=role_id,
            guild_id=guild_id
        )
        result = await db.execute(stmt)
        permission = result.scalar_one_or_none()

        if permission:
            await db.delete(permission)
            await db.commit()
            logger.info(f"INFO Запись о примененных правах успешно удалена")
            return {"status": "Запись удалена"}
        else:
            raise HTTPException(status_code=404, detail="Запись не найдена")
    
    except Exception as e:
        logger.error(f"Ошибка при удалении записи о примененных правах: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении записи о примененных правах")
