# game_server/api_fast/rest_routers/system/system_mapping.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
import logging # Используем стандартный модуль logging

# Импорты Pydantic моделей для запросов и ответов
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response
from game_server.api_fast.api_models.system_api import StateEntityAPIResponse

# Импорт сервисного слоя (бизнес-логики) из ApplicationLogic
from game_server.Logic.ApplicationLogic.DiscordIntegration.state_entities_logic import StateEntitiesLogic

# Импорт новых DTO-моделей из common_contracts
from game_server.common_contracts.discord_integration.discord_commands_and_events import (
    StateEntityDTO,
    StateEntityGetByAccessCodeCommand,
    StateEntityUpdateCommand # Если этот роут будет добавлен
)

# Импорт общих зависимостей из api_fast/dependencies.py
from api_fast.dependencies import (
    get_state_entities_logic # Теперь импортируем из dependencies
)

logger = logging.getLogger(__name__) # Инициализация логгера для данного модуля

router = APIRouter()

@router.get(
    "/state-entities",
    response_model=APIResponse[List[StateEntityAPIResponse]],
    summary="Получить все сущности состояний",
    description="Возвращает список всех сущностей состояний (ролей, флагов) из базы данных."
)
async def get_all_states(
    state_entities_logic: StateEntitiesLogic = Depends(get_state_entities_logic) # ИСПОЛЬЗУЕМ ЗАВИСИМОСТЬ ЛОГИКИ
) -> APIResponse[List[StateEntityAPIResponse]]:
    logger.info("Запрос на получение всех State Entities из БД.")
    try:
        # Бизнес-логика теперь возвращает список DTO-моделей
        states_data_from_logic: List[StateEntityDTO] = await state_entities_logic.get_all_state_entities()
        
        # Преобразуем DTO-модели в список Pydantic API-моделей для ответа
        states_response_models = [StateEntityAPIResponse.model_validate(state.model_dump()) for state in states_data_from_logic]

        return create_success_response(data=states_response_models, message="Список сущностей состояний успешно получен.")
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении всех сущностей состояний: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при получении данных.").model_dump()
        )

@router.get(
    "/state-entities/{access_code}",
    response_model=APIResponse[StateEntityAPIResponse],
    summary="Получить сущность состояния по access_code",
    description="Возвращает данные сущности состояния по её буквенно-цифровому access_code."
)
async def get_state_by_access_code(
    access_code: str,
    state_entities_logic: StateEntitiesLogic = Depends(get_state_entities_logic) # ИСПОЛЬЗУЕМ ЗАВИСИМОСТЬ ЛОГИКИ
) -> APIResponse[StateEntityAPIResponse]:
    logger.info(f"Запрос на получение State Entity по access_code: {access_code}.")
    try:
        # 1. Преобразование входящего параметра в Internal DTO Command
        get_command = StateEntityGetByAccessCodeCommand(access_code=access_code)

        # 2. Вызов бизнес-логики, которая теперь возвращает DTO-модель или None
        state_data_from_logic: Optional[StateEntityDTO] = await state_entities_logic.get_state_by_access_code(get_command)
        
        if state_data_from_logic is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=create_error_response(code="NOT_FOUND", message=f"Сущность с access_code '{access_code}' не найдена.").model_dump()
            )
        
        # 3. Преобразуем DTO-модель в Pydantic API-модель для ответа
        state_response_model = StateEntityAPIResponse.model_validate(state_data_from_logic.model_dump())

        return create_success_response(data=state_response_model, message=f"Сущность '{access_code}' успешно получена.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении сущности по access_code '{access_code}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=create_error_response(code="INTERNAL_SERVER_ERROR", message="Произошла внутренняя ошибка сервера при получении данных.").model_dump()
        )

system_mapping_router = router