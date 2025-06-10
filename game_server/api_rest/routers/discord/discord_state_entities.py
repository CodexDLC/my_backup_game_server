# app/api/v1/endpoints/discord_entities.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

# Убедитесь, что пути импорта верны для вашего проекта
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session



# Логгер, если он нужен в роутах
from game_server.services.logging.logging_setup import logger
from game_server.Logic.InterfacesLogic.Discord.Discord_State_Entities_logic import StateEntitiesDiscordLogic
from game_server.database.models.pandemic_models import StateEntitiesDiscordBase, StateEntitiesDiscordCreateUpdateRequest, StateEntitiesDiscordResponse

router = APIRouter()

# --- GET /discord/entities/{guild_id} ---
@router.get(
    "/entities/{guild_id}",
    summary="Получить все записи сущностей для гильдии",
    response_model=List[StateEntitiesDiscordResponse] # Указываем ожидаемую модель ответа
)
async def get_all_entities_for_guild_route(
    guild_id: int,
    db_session: AsyncSession = Depends(get_db_session) # 🔑 Инъекция сессии БД
) -> List[StateEntitiesDiscordResponse]:
    """
    Получает все записи `state_entities_discord` для конкретной гильдии.
    """
    # 🔑 Создаем экземпляр логики, передавая сессию БД
    logic = StateEntitiesDiscordLogic(db_session)
    result = await logic.get_all_entities_for_guild(guild_id)

    if result["status"] == "found":
        # Если get_all_entities_for_guild теперь возвращает Row objects,
        # FastAPI/Pydantic автоматически преобразует их в List[StateEntitiesDiscordResponse]
        return result["data"]
    elif result["status"] == "error":
        logger.error(f"❌ Ошибка в роуте get_all_entities_for_guild_route: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    else:
        return [] # Возвращаем пустой список, если "not_found" или другой статус

# --- GET /discord/entity_by_pk/{guild_id}/{world_id}/{access_code} ---
@router.get(
    "/entity_by_pk/{guild_id}/{world_id}/{access_code}",
    summary="Получить запись сущности по первичному ключу",
    response_model=StateEntitiesDiscordResponse # Возвращает одну сущность
)
async def get_entity_by_primary_key_route(
    guild_id: int,
    world_id: str,
    access_code: int,
    db_session: AsyncSession = Depends(get_db_session)
) -> StateEntitiesDiscordResponse:
    """
    Получает одну запись `state_entities_discord` по составному первичному ключу.
    """
    logic = StateEntitiesDiscordLogic(db_session)
    result = await logic.get_entity_by_primary_key(guild_id, world_id, access_code)

    if result["status"] == "found":
        return result["data"]
    elif result["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    else:
        logger.error(f"❌ Ошибка в роуте get_entity_by_primary_key_route: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

# --- PUT /discord/update_by_pk/{guild_id}/{world_id}/{access_code} ---
@router.put(
    "/update_by_pk/{guild_id}/{world_id}/{access_code}",
    summary="Обновить запись сущности по первичному ключу",
    response_model=StateEntitiesDiscordResponse # Возвращает обновленную сущность или статус
)
async def update_entity_route(
    guild_id: int,
    world_id: str,
    access_code: int,
    entity_data: StateEntitiesDiscordCreateUpdateRequest, # Pydantic модель для входящих данных
    db_session: AsyncSession = Depends(get_db_session)
) -> StateEntitiesDiscordResponse:
    """
    Обновляет запись `state_entities_discord` по составному первичному ключу.
    """
    logic = StateEntitiesDiscordLogic(db_session)
    result = await logic.update_entity_by_primary_key(guild_id, world_id, access_code, entity_data.model_dump()) # ИЛИ entity_data.dict() для Pydantic v1

    if result["status"] == "success":
        return result["data"] # Возвращаем обновленные данные
    elif result["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    else:
        logger.error(f"❌ Ошибка в роуте update_entity_route: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

# --- DELETE /discord/delete_by_pk/{guild_id}/{world_id}/{access_code} ---
@router.delete(
    "/delete_by_pk/{guild_id}/{world_id}/{access_code}",
    summary="Удалить запись сущности по первичному ключу",
    status_code=status.HTTP_204_NO_CONTENT # Указываем, что при успешном удалении не возвращаем контент
)
async def delete_entity_route(
    guild_id: int,
    world_id: str,
    access_code: int,
    db_session: AsyncSession = Depends(get_db_session)
) -> None: # Возвращает None, так как 204 No Content
    """
    Удаляет запись `state_entities_discord` по составному первичному ключу.
    """
    logic = StateEntitiesDiscordLogic(db_session)
    result = await logic.delete_entity_by_primary_key(guild_id, world_id, access_code)

    if result["status"] == "success":
        return # FastAPI автоматически вернет 204 No Content
    elif result["status"] == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["message"]
        )
    else:
        logger.error(f"❌ Ошибка в роуте delete_entity_route: {result['message']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

# --- POST /discord/create_roles/ ---
@router.post(
    "/create_roles/",
    summary="Массовое создание/обновление ролей",
    response_model=Dict[str, Any] # Или более специфичная модель ответа, если есть
)
async def create_roles_discord_route(
    roles_batch: List[StateEntitiesDiscordCreateUpdateRequest], # Ожидаем список Pydantic моделей
    db_session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Массовое добавление или обновление записей ролей в БД (UPSERT).
    """
    logic = StateEntitiesDiscordLogic(db_session)
    
    # Преобразуем список Pydantic-моделей в список словарей для передачи в логику
    processed_roles = [role.model_dump() for role in roles_batch] # ИЛИ role.dict() для Pydantic v1

    result = await logic.create_roles_discord(processed_roles)

    if result.get("error"): # Проверяем на ключ "error"
        logger.error(f"❌ Ошибка в роуте create_roles_discord_route: {result['error']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Или 500 в зависимости от типа ошибки
            detail=result["error"]
        )
    return result


@router.post(
    "/create_roles/",
    summary="Массовое добавление/обновление записей для Discord-ролей (UPSERT)",
    response_model=Dict[str, Any]
)
async def create_roles_route(
    roles_batch: List[StateEntitiesDiscordCreateUpdateRequest], # <-- ЭТО ВАЖНО!
    db_session: Any = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Массовое добавление/обновление записей `state_entities_discord` (UPSERT).
    Предназначен для создания или обновления данных о Discord-ролях.
    """
    logic = StateEntitiesDiscordLogic(db_session)

    # Здесь будет список словарей БЕЗ guild_id, как вы и хотите
    formatted_batch = [item.model_dump() for item in roles_batch]

    # Теперь ваша функция logic.create_roles_discord должна будет
    # сама понять, как получить guild_id (например, из контекста бота)
    # и добавить его к каждому элементу перед сохранением в БД.
    result = await logic.create_roles_discord(formatted_batch)

    if result.get("status") == "success":
        return result
    elif "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Непредвиденная ошибка при массовом добавлении/обновлении ролей."
        )

# Экспортируем роутер
state_entities_discord_router = router