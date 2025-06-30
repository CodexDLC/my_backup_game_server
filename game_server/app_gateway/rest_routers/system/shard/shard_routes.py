# game_server/app_gateway/rest_routers/system/shard_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.config.logging.logging_setup import app_logger as logger

# Импорт моделей
from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO
from game_server.common_contracts.shared_models.api_contracts import APIResponse, SuccessResponse

router = APIRouter(tags=["Shard Management"])

@router.post(
    "/register",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать регистрацию игрового шарда"
)
async def register_game_shard_endpoint(
    request_data: SaveShardCommandDTO,
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Принимает запрос на регистрацию шарда, отправляет команду в SystemServices
    и немедленно возвращает 202 Accepted.
    """
    logger.info(f"Получен REST-запрос на регистрацию шарда: Guild ID={request_data.discord_guild_id}.")
    
    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    # 🔥 ИЗМЕНЕНИЕ: Routing key теперь соответствует 'system.save_shard'
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.system.save_shard" # 🔥🔥 КЛЮЧЕВОЕ ИЗМЕНЕНИЕ

    try:
        # 🔥 ИЗМЕНЕНИЕ: Имя команды в логе теперь 'system:save_shard'
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'system:save_shard' для шарда {request_data.shard_name} (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message="Команда на регистрацию шарда принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'system:save_shard': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")

shard_router = router
