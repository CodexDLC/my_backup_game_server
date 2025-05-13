from fastapi import APIRouter, HTTPException, Depends
from game_server.database.models.models import StateEntities
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session  # Подключаем сессию SQLAlchemy
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

router = APIRouter()

# -------------------- Модели запроса --------------------
class RoleCreateRequest(BaseModel):
    access_code: str
    role_name: str
    permissions: int

class CreateRoleRequest(BaseModel):
    guild_id: int
    world_id: str
    roles: List[RoleCreateRequest]

class RoleResponse(BaseModel):
    access_code: str
    role_name: str
    permissions: int


# -------------------- POST /create_roles --------------------
@router.post("/create_roles", summary="Создать роли для Discord")
async def create_roles(payload: CreateRoleRequest, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Создание ролей для guild_id={payload.guild_id}, world_id={payload.world_id}")
    
    try:
        for role in payload.roles:
            # Создаем роль через SQLAlchemy
            new_role = StateEntities(
                access_code=role.access_code,
                role_name=role.role_name,
                permissions=role.permissions
            )
            db.add(new_role)
        
        await db.commit()  # Сохраняем изменения
        logger.info(f"INFO Роли для guild_id={payload.guild_id} успешно созданы")
        return {"status": "Роли успешно созданы"}
    
    except Exception as e:
        logger.error(f"Ошибка при создании ролей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при создании ролей")


# -------------------- GET /list_roles/{guild_id} --------------------
@router.get("/list_roles/{guild_id}", response_model=List[RoleResponse], summary="Получить все роли для указанной гильдии")
async def list_roles(guild_id: int, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Запрос на получение ролей для guild_id={guild_id}")
    
    try:
        # Выполняем запрос через SQLAlchemy
        stmt = select(StateEntities).filter_by(guild_id=guild_id)
        result = await db.execute(stmt)
        rows = result.scalars().all()
        
        if not rows:
            logger.info(f"⚠️ Роли для guild_id={guild_id} не найдены")
            return []
        
        return [RoleResponse(**dict(r)) for r in rows]
    
    except Exception as e:
        logger.error(f"Ошибка при получении ролей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении ролей")


# -------------------- DELETE /delete_role/{guild_id}/{access_code} --------------------
@router.delete("/delete_role/{guild_id}/{access_code}", summary="Удалить роль по guild_id и access_code")
async def delete_role(guild_id: int, access_code: int, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Удаление роли для guild_id={guild_id}, access_code={access_code}")
    
    try:
        stmt = select(StateEntities).filter_by(guild_id=guild_id, access_code=access_code)
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()

        if role:
            await db.delete(role)
            await db.commit()  # Удаляем роль
            logger.info(f"INFO Роль с access_code={access_code} для guild_id={guild_id} успешно удалена")
            return {"status": "Роль удалена"}
        else:
            raise HTTPException(status_code=404, detail="Роль не найдена")
    
    except Exception as e:
        logger.error(f"Ошибка при удалении роли: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении роли")


# -------------------- DELETE /delete_all_roles/{guild_id} --------------------
@router.delete("/delete_all_roles/{guild_id}", summary="Удалить все роли для указанной гильдии")
async def delete_all_roles(guild_id: int, db: AsyncSession = Depends(get_db_session)):
    logger.info(f"Удаление всех ролей для guild_id={guild_id}")
    
    try:
        stmt = select(StateEntities).filter_by(guild_id=guild_id)
        result = await db.execute(stmt)
        roles = result.scalars().all()

        if roles:
            for role in roles:
                await db.delete(role)  # Удаляем все роли для guild_id
            await db.commit()  # Коммитим изменения
            logger.info(f"INFO Все роли для guild_id={guild_id} успешно удалены")
            return {"status": "Все роли удалены"}
        else:
            raise HTTPException(status_code=404, detail="Роли не найдены")
    
    except Exception as e:
        logger.error(f"Ошибка при удалении всех ролей: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении всех ролей")
