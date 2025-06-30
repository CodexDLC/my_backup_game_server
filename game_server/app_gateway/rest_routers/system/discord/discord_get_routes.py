# game_server/app_gateway/rest_routers/system/discord_get_routes.py

from fastapi import APIRouter, Depends, HTTPException, status, Header
from typing import Annotated, Any

# Импорты наших стандартных компонентов
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys
from game_server.config.logging.logging_setup import app_logger as logger

# Импорты моделей запроса и ответа
from game_server.common_contracts.api_models.discord_api import GetDiscordEntitiesRequest
from game_server.common_contracts.shared_models.api_contracts import APIResponse, SuccessResponse

router = APIRouter(tags=["Discord Management"])

@router.post(
    "/get",
    response_model=APIResponse[SuccessResponse],
    status_code=status.HTTP_202_ACCEPTED,
    summary="Инициировать запрос на получение сущностей Discord"
)
async def get_discord_entities_by_guild_endpoint(
    request_data: GetDiscordEntitiesRequest,
    message_bus: Annotated[IMessageBus, Depends(get_message_bus_dependency)],
    # ✅ СТАНДАРТ: Принимаем ID клиента через обязательный заголовок
    x_client_id: Annotated[str | None, Header()] = None
) -> APIResponse[SuccessResponse]:
    """
    Принимает команду на получение сущностей Discord, отправляет ее в шину
    и немедленно возвращает 202 Accepted. Результат придет по WebSocket.
    """
    logger.info(f"Получен REST-запрос на получение сущностей для гильдии {request_data.guild_id}. Correlation ID: {request_data.correlation_id}")
    
    # 1. ✅ СТАНДАРТ: Валидация наличия ID клиента
    if not x_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HTTP заголовок 'X-Client-ID' является обязательным."
        )

    # 2. ✅ СТАНДАРТ: Формируем payload из DTO запроса
    command_payload = request_data.model_dump()
    
    # 3. ✅ СТАНДАРТ: ОБОГАЩАЕМ PAYLOAD, добавляя client_id для обратной связи.
    # Это самый важный шаг для асинхронного ответа.
    command_payload['client_id'] = x_client_id
    
    # 4. ✅ СТАНДАРТ: Формируем семантический ключ маршрутизации
    # Пример: command.system.get_entities
    routing_key = f"{RoutingKeys.COMMAND_PREFIX}.system.get_entities"
    
    try:
        # 5. Публикуем обогащенный payload
        await message_bus.publish(
            exchange_name=Exchanges.COMMANDS,
            routing_key=routing_key,
            message=command_payload 
        )
        logger.info(f"Команда 'get_entities' для гильдии {request_data.guild_id} (CorrID: {request_data.correlation_id}) опубликована.")

        # 6. ✅ СТАНДАРТ: Возвращаем немедленный успешный ответ
        return APIResponse(
            success=True,
            message="Команда на получение сущностей принята к обработке.",
            data=SuccessResponse(correlation_id=request_data.correlation_id)
        )

    except Exception as e:
        logger.error(f"Ошибка при публикации команды 'get_entities': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при отправке команды в шину сообщений."
        )

# Экспортируем роутер
discord_get_router = router
