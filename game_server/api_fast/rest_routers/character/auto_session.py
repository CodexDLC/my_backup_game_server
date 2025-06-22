# rest_routers/character/auto_session.py
from fastapi import APIRouter, Depends, HTTPException, status # Добавляем HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging # Для логирования ошибок

from game_server.api_fast.api_models.character_api import AutoSessionRequest, AutoSessionData
from game_server.api_fast.dependencies import get_db_session
from game_server.api_fast.api_models.response_api import APIResponse, create_error_response, create_success_response
# from .character_parsers import parse_auto_session # <--- УДАЛЯЕМ, если он не нужен для сложного парсинга

from game_server.Logic.DomainLogic.CharacterLogic.auto_session.autosesion import AutoSession

router = APIRouter()
logger = logging.getLogger(__name__) # Инициализация логгера

@router.post("/handle", response_model=APIResponse[AutoSessionData])
async def handle_session(
    request_data_pydantic: AutoSessionRequest, # <--- ПРИНИМАЕМ Pydantic-модель НАПРЯМУЮ КАК ТЕЛО ЗАПРОСА
    db_session: AsyncSession = Depends(get_db_session)
):
    # --- Слой преобразования: Pydantic-модель в словарь ---
    # Преобразуем входящую Pydantic-модель в обычный Python-словарь
    # для передачи в бизнес-логику, которая не должна знать о Pydantic.
    request_data_for_logic = request_data_pydantic.model_dump() # Используем .model_dump() для Pydantic v2
    logger.info(f"Получены и преобразованы данные для AutoSession: {request_data_for_logic.get('action')}")
    logger.debug(f"Полные данные для AutoSession: {request_data_for_logic}")
    # -----------------------------------------------------

    try:
        auto_session_service = AutoSession(db_session)
        # Передаем обычные данные (элементы словаря) в бизнес-логику
        result = await auto_session_service.handle(
            request_data_for_logic.get("action"),
            request_data_for_logic.get("identifier_type"),
            request_data_for_logic.get("identifier_value"),
            request_data_for_logic.get("category")
        )
        
        # Предполагаем, что сервис возвращает словарь, который мы упаковываем в Pydantic модель для ответа
        response_data = AutoSessionData(**result)
        return create_success_response(data=response_data)

    except ValueError as e: # Обработка ожидаемых ошибок из бизнес-логики
        logger.warning(f"Ошибка валидации запроса в AutoSession: {e}")
        # Возвращаем 400 Bad Request, так как это проблема с клиентскими данными
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=create_error_response(code="INVALID_REQUEST", message=str(e)).model_dump()
        )
    except Exception as e:
        logger.critical(f"Непредвиденная ошибка в AutoSession: {e}", exc_info=True)
        # Возвращаем 500 Internal Server Error для непредвиденных ошибок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Internal server error").model_dump()
        )

auto_session_router = router