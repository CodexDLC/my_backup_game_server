import json
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Callable # Добавил Callable, если вдруг где-то все же потребуется передать функцию

# Импортируем наш переработанный DiscordBindingLogic
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from game_server.Logic.InterfacesLogic.Discord.discord_binding_logic import DiscordBindingLogic

from game_server.database.models.pandemic_models import GetAllBindingsResponse
from game_server.services.logging.logging_setup import logger

# Импортируем вашу функцию для получения сессии, которая является асинхронным генератором
 # Используем db_session.py как вы указали

router = APIRouter()

# ---
# Роут для массовой вставки/обновления привязок
@router.post("/upsert", summary="Создать или обновить привязки Discord")
async def upsert_bindings_route(
    binding_data: list[dict] = Body(...),
    # 🔥 ИЗМЕНЕНИЕ: FastAPI сам вызовет get_db_session() и передаст **готовую AsyncSession**
    db_session: AsyncSession = Depends(get_db_session)
):
    logger.info(f"Получен запрос на UPSERT {len(binding_data)} привязок.")
    
    try:
        # Инициализируем DiscordBindingLogic, передавая ему уже готовую сессию
        logic = DiscordBindingLogic(db_session) # <--- ПЕРЕДАЕМ ГОТОВУЮ СЕССИЮ
        processed_count = await logic.upsert_discord_bindings(binding_data)
        logger.info(f"Успешно обработано {processed_count} привязок через API.")
        return {"status": "success", "message": f"Обработано {processed_count} привязок.", "processed_count": processed_count}
    except ValueError as e:
        logger.error(f"Ошибка валидации данных в запросе UPSERT: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка валидации данных: {e}"
        )
    except Exception as e:
        logger.error(f"Внутренняя ошибка сервера при UPSERT привязок: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {e}"
        )
    
# ---
# Роут для получения одной привязки по guild_id и access_key
@router.get("/{guild_id}/{access_key}", summary="Получить привязку по guild_id и access_key")
async def get_binding_by_key_route(
    guild_id: int,
    access_key: str,
    # 🔥 ИЗМЕНЕНИЕ: Передаем готовую AsyncSession
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Получает одну привязку для указанной гильдии по её уникальному access_key.
    """
    logger.info(f"Получен запрос на получение привязки для guild_id={guild_id}, access_key='{access_key}'.")
    try:
        # Инициализируем DiscordBindingLogic, передавая ему уже готовую сессию
        logic = DiscordBindingLogic(db_session) # <--- ПЕРЕДАЕМ ГОТОВУЮ СЕССИЮ
        binding = await logic.get_binding_by_key(guild_id, access_key)
        if binding:
            return {"status": "found", "data": binding}
        
        logger.warning(f"Привязка не найдена для guild_id={guild_id}, access_key='{access_key}'.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Привязка не найдена."
        )
    except Exception as e:
        logger.error(f"Ошибка при получении привязки через API (guild_id={guild_id}, access_key='{access_key}'): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {e}"
        )
    
@router.get(
    "/guild/{guild_id}/all",
    response_model=GetAllBindingsResponse, # <--- ЭТО САМОЕ ВАЖНОЕ ИЗМЕНЕНИЕ!
    summary="Получить все привязки для указанной гильдии",
    description="Возвращает список всех привязок Discord категорий и каналов для конкретной гильдии.",
    response_description="Список привязок Discord"
)
async def get_all_bindings_for_guild_route(
    guild_id: int,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Получает все Discord-привязки (для категорий и каналов) для указанной гильдии.
    """
    logger.info(f"Получен запрос на получение всех привязок для guild_id={guild_id}.")
    try:
        logic = DiscordBindingLogic(db_session)
        bindings = await logic.get_all_bindings(guild_id) # Это вернет List[DiscordBindings ORM Model]

        logger.info(f"API готов вернуть данные для guild_id={guild_id}. Количество привязок: {len(bindings)}. Данные: {bindings}")

        # FastAPI теперь автоматически использует GetAllBindingsResponse для валидации и сериализации
        # Он возьмет объекты DiscordBindings из 'bindings' и преобразует их в DiscordBindingResponse
        return {"status": "success", "data": bindings}

    except Exception as e:
        logger.error(f"Ошибка при получении всех привязок через API для guild_id={guild_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {e}"
        )


# ---
# Роут для удаления привязки по guild_id и access_key
@router.delete("/{guild_id}/{access_key}", summary="Удалить привязку")
async def delete_binding_route(
    guild_id: int,
    access_key: str,
    # 🔥 ИЗМЕНЕНИЕ: Передаем готовую AsyncSession
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Удаляет привязку для указанной гильдии по её уникальному access_key.
    """
    logger.info(f"Получен запрос на удаление привязки для guild_id={guild_id}, access_key='{access_key}'.")
    try:
        # Инициализируем DiscordBindingLogic, передавая ему уже готовую сессию
        logic = DiscordBindingLogic(db_session) # <--- ПЕРЕДАЕМ ГОТОВУЮ СЕССИЮ
        deleted = await logic.delete_discord_binding(guild_id, access_key)
        if deleted:
            logger.info(f"Привязка (guild_id={guild_id}, access_key='{access_key}') успешно удалена через API.")
            return {"status": "success", "message": "Привязка успешно удалена."}
        
        logger.warning(f"Привязка (guild_id={guild_id}, access_key='{access_key}') не найдена для удаления через API.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Привязка не найдена для удаления."
        )
    except Exception as e:
        logger.error(f"Ошибка при удалении привязки через API (guild_id={guild_id}, access_key='{access_key}'): {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Внутренняя ошибка сервера: {e}"
        )

# ---
# Экземпляр роутера, который будет использоваться в главном приложении FastAPI
discord_bindings_router = router