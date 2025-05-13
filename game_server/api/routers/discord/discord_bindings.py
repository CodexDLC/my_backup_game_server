import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from game_server.database.models.models import AppliedPermissions, DiscordBindings
from game_server.services.logging_config import logger
from game_server.Logic.DataAccessLogic.db_instance import get_db_session  # Импортируем функцию для сессии SQLAlchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

router = APIRouter()

# -------------------- Модель запроса --------------------
class BindingRequest(BaseModel):
    world_id: UUID
    category_id: Optional[str] = None
    channel_id: Optional[str] = None

# -------------------- Ответ для привязки --------------------
class BindingResponse(BaseModel):
    entity_access_key: str
    category_id: Optional[str]
    channel_id: Optional[str]
    world_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {
        "arbitrary_types_allowed": True
    }

# -------------------- Ответ для прав доступа --------------------
class PermissionResponse(BaseModel):
    discord_role_id: str
    discord_channel_id: str
    permissions: int


# -------------------- POST /bindings --------------------
@router.post(
    "/bindings/{guild_id}/{entity_access_key}",
    summary="Сохранить или обновить привязку Discord",
)
async def save_binding(
    guild_id: int,
    entity_access_key: str,
    payload: BindingRequest,
    db: AsyncSession = Depends(get_db_session)  # Подключаем сессию SQLAlchemy
):
    logger.info(f"📝 Сохранение привязки: guild={guild_id}, key={entity_access_key}, world_id={payload.world_id}")

    try:
        # С использованием SQLAlchemy
        stmt = select(DiscordBindings).filter_by(guild_id=guild_id, entity_access_key=entity_access_key)
        result = await db.execute(stmt)
        existing_binding = result.scalar_one_or_none()

        if existing_binding:
            # Если привязка существует, обновляем её
            existing_binding.category_id = payload.category_id
            existing_binding.channel_id = payload.channel_id
            existing_binding.updated_at = datetime.datetime.utcnow()
            db.add(existing_binding)
        else:
            # Если привязка не существует, создаем новую
            new_binding = DiscordBindings(
                guild_id=guild_id,
                world_id=payload.world_id,
                entity_access_key=entity_access_key,
                category_id=payload.category_id,
                channel_id=payload.channel_id,
                created_at=datetime.datetime.utcnow(),
                updated_at=datetime.datetime.utcnow()
            )
            db.add(new_binding)

        await db.commit()
        logger.info(f"INFO Привязка сохранена: {entity_access_key} для world_id={payload.world_id}")
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"ERROR Ошибка при сохранении привязки: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при сохранении привязки")


# -------------------- GET /bindings --------------------
@router.get(
    "/bindings/{guild_id}",
    response_model=List[BindingResponse],
    summary="Получить все привязки Discord для указанной гильдии"
)
async def get_bindings(
    guild_id: int,
    db: AsyncSession = Depends(get_db_session)  # Подключаем сессию SQLAlchemy
):
    logger.info(f"📥 Запрос привязок для guild_id={guild_id}")

    try:
        stmt = select(DiscordBindings).filter_by(guild_id=guild_id).order_by(DiscordBindings.entity_access_key)
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.info(f"⚠️ Привязки для guild_id={guild_id} не найдены. Возможно, эта гильдия еще не настроена.")
            return []  # Возвращаем пустой список, так как данных нет

        logger.info(f"INFO Найдено {len(rows)} привязок для guild_id={guild_id}")
        return [BindingResponse(**dict(row)) for row in rows]

    except Exception as e:
        logger.error(f"ERROR Ошибка при получении привязок: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении привязок")


# -------------------- GET /permissions --------------------
@router.get(
    "/permissions/{entity_access_key}",
    response_model=List[PermissionResponse],
    summary="Получить битовый флаг прав для указанного access_key"
)
async def get_permissions(
    entity_access_key: str,
    db: AsyncSession = Depends(get_db_session)  # Подключаем сессию SQLAlchemy
):
    logger.info(f"🔐 Запрос прав доступа для entity_access_key={entity_access_key}")

    try:
        stmt = select(AppliedPermissions).filter_by(entity_access_key=entity_access_key).order_by(AppliedPermissions.role_id)
        result = await db.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            # вместо 404 возвращаем пустой список
            logger.info(f"ℹ️ Прав для {entity_access_key} не найдено, верну пустой список")
            return []

        return [PermissionResponse(**dict(r)) for r in rows]
    
    except Exception as e:
        logger.error(f"ERROR Ошибка при получении прав доступа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении прав доступа")
