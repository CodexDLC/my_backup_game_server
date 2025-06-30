# game_server\app_gateway\rest_routers\system\discord\discord_config_sync_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated


from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
# Добавляем импорт GuildConfigDeleteRequest
from game_server.common_contracts.api_models.discord_api import GuildConfigSyncRequest, GuildConfigDeleteRequest
from game_server.common_contracts.shared_models.api_contracts import APIResponse, SuccessResponse
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.config.logging.logging_setup import app_logger as logger


router = APIRouter(tags=["Discord Management"])

@router.post(
    "/guild-config/sync",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать синхронизацию сущностей Discord"
)
async def sync_config_from_bot_endpoint(
    request_data: GuildConfigSyncRequest,
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Принимает запрос на синхронизацию, отправляет команду в SystemServices
    и немедленно возвращает 202 Accepted.
    """
    logger.info(f"Получен REST-запрос на sync для гильдии {request_data.guild_id}.")
    
    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    # Меняем двоеточие на точку в routing_key для соответствия шаблону привязки
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.discord.sync_config_from_bot"
    
    try:
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'sync_config_from_bot' для гильдии {request_data.guild_id} (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message="Команда на синхронизацию принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'sync_config_from_bot': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")
    

# НОВЫЙ ЭНДПОИНТ: Для удаления конфигурации гильдии из бэкенд-Redis
@router.post(
    "/guild-config/delete", # Новый путь для удаления
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать удаление конфигурации гильдии из бэкенд-кэша"
)
async def delete_config_from_bot_endpoint(
    request_data: GuildConfigDeleteRequest, # Используем новый DTO
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Принимает запрос на удаление конфигурации, отправляет команду в SystemServices
    и немедленно возвращает 202 Accepted.
    """
    logger.info(f"Получен REST-запрос на удаление конфигурации для гильдии {request_data.guild_id}.")

    if not x_client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="HTTP заголовок 'X-Client-ID' является обязательным.")

    command_payload = request_data.model_dump()
    command_payload['client_id'] = x_client_id
    
    # Routing key для новой команды удаления
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.discord.delete_config_from_bot" # Новый routing key
    
    try:
        await message_bus.publish(Exchanges.COMMANDS, routing_key, command_payload)
        logger.info(f"Команда 'delete_config_from_bot' для гильдии {request_data.guild_id} (CorrID: {request_data.correlation_id}) опубликована.")
        return APIResponse(success=True, message="Команда на удаление конфигурации принята.", data=SuccessResponse(correlation_id=request_data.correlation_id))
    except Exception as e:
        logger.error(f"Ошибка публикации команды 'delete_config_from_bot': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка отправки команды.")


discord_config_sync_routes = router
