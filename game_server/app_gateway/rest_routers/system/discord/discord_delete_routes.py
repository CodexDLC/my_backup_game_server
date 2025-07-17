# game_server/app_gateway/rest_routers/system/discord_delete_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.contracts.api_models.discord.entity_management_requests import UnifiedEntityBatchDeleteRequest
from game_server.contracts.shared_models.base_responses import APIResponse, SuccessResponse

# Импорт моделей

router = APIRouter(tags=["Discord Management"])

@router.delete(
    "/batch-delete",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать пакетное удаление сущностей Discord"
)
async def delete_discord_entities_batch_endpoint(
    request_data: UnifiedEntityBatchDeleteRequest,
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Принимает запрос на пакетное удаление, отправляет команду в SystemServices
    и немедленно возвращает 202 Accepted.
    """
    logger.info(f"Получен REST-запрос на batch-delete для гильдии {request_data.guild_id}.")
    
    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.system.delete_entities"
    
    try:
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'delete_entities' для гильдии {request_data.guild_id} (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message="Команда на удаление принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'delete_entities': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")

discord_delete_router = router
