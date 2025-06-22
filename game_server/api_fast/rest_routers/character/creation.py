# rest_routers/character/creation.py
from fastapi import APIRouter, Depends, HTTPException, status # Добавляем HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from game_server.api_fast.api_models.character_api import CharacterCreateRequest, CharacterCreateData
from game_server.api_fast.dependencies import get_db_session, get_character_cache_manager
from game_server.api_fast.api_models.response_api import APIResponse, create_error_response, create_success_response
# from .character_parsers import parse_character_creation # <--- УДАЛЯЕМ, если он не нужен для сложного парсинга

from game_server.Logic.DomainLogic.CharacterLogic.character_creation import CharacterCreationOrchestrator
from game_server.Logic.InfrastructureLogic.app_cache.services.character.character_cache_manager import CharacterCacheManager

router = APIRouter()
logger = logging.getLogger(__name__) # Инициализация логгера

@router.post("/create", response_model=APIResponse[CharacterCreateData])
async def create_character_for_account(
    request_data_pydantic: CharacterCreateRequest, # <--- ПРИНИМАЕМ Pydantic-модель НАПРЯМУЮ КАК ТЕЛО ЗАПРОСА
    session: AsyncSession = Depends(get_db_session),
    cache_manager: CharacterCacheManager = Depends(get_character_cache_manager)
):
    # --- Слой преобразования: Pydantic-модель в словарь ---
    # Преобразуем входящую Pydantic-модель в обычный Python-словарь
    # для передачи в бизнес-логику, которая не должна знать о Pydantic.
    character_data_for_logic = request_data_pydantic.model_dump() # Используем .model_dump() для Pydantic v2
    logger.info(f"Получены и преобразованы данные для создания персонажа.")
    logger.debug(f"Полные данные для создания персонажа: {character_data_for_logic}")
    # -----------------------------------------------------

    try:
        orchestrator = CharacterCreationOrchestrator(session, cache_manager)
        
        # Передаем обычные данные (словарь) в бизнес-логику.
        # Если orchestrator.execute ожидает только discord_id, извлекаем его здесь.
        # Если он ожидает весь словарь, передаем весь словарь.
        # Предположим, что он ожидает dict.
        new_character_data = await orchestrator.execute(character_data_for_logic) 
        
        # Если 'async with session.begin():' не внутри orchestrator.execute,
        # то логика транзакции может быть здесь, или в более высоком слое (middleware).
        # Но для "тонкого роута" лучше, чтобы orchestrator сам управлял транзакцией,
        # если он выполняет несколько операций с БД.
        
        await orchestrator.character_cache_manager.decrement_pool_count()
        
        # Предполагаем, что orchestrator.execute возвращает данные, 
        # которые можно использовать для CharacterCreateData.
        # Если new_character_data это ORM объект, возможно, понадобится model_dump()
        # new_character_data = new_character.model_dump() # Если new_character - это ORM объект
        response_data = CharacterCreateData(**new_character_data) # Если new_character_data - это уже словарь
        return create_success_response(data=response_data)

    except ValueError as e:
        logger.warning(f"Ошибка валидации запроса при создании персонажа: {e}")
        error_code = "NOT_FOUND" if "not found" in str(e).lower() else "CONFLICT" # Логика определения кода ошибки должна быть в сервисе
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code=error_code, message=str(e)).model_dump()
        )
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка при создании персонажа: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

character_creation_router = router