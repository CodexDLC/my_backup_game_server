# game_server/app_gateway/rest_routers/system/state_entity_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.contracts.api_models.system.requests import GetAllStateEntitiesRequest, GetStateEntityByKeyRequest
from game_server.contracts.shared_models.base_responses import APIResponse, SuccessResponse

# Импорт моделей


router = APIRouter(tags=["State Entity Management"])

@router.post(
    "/get-all",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать запрос на получение всех сущностей состояния"
)
async def request_all_state_entities_endpoint(
    request_data: GetAllStateEntitiesRequest, # <-- ИЗМЕНЕНО с BaseRequest на GetAllStateEntitiesRequest
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    # ... остальной код функции остается прежним, так как request_data.model_dump()
    # теперь будет корректно включать 'command'
    logger.info(f"Получен REST-запрос на get-all state-entities.")

    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    # Теперь request_data.model_dump() будет включать "command"
    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.system.get_all_state_entities"
    
    try:
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'get_all_state_entities' (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message="Команда на получение всех сущностей принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'get_all_state_entities': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")

@router.post(
    "/get-by-key",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать запрос на получение сущности состояния по ключу"
)
async def request_state_entity_by_key_endpoint(
    request_data: GetStateEntityByKeyRequest,
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Отправляет команду на получение сущности состояния по ключу и немедленно возвращает 202.
    """
    logger.info(f"Получен REST-запрос на get-by-key для ключа '{request_data.key}'.")
    
    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.system.get_state_entity_by_key"
    
    try:
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'get_state_entity_by_key' для ключа '{request_data.key}' (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message=f"Команда для ключа '{request_data.key}' принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'get_state_entity_by_key': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")

state_entity_router = router
