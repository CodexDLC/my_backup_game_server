# game_server/app_gateway/rest_routers/gateway/command_routes.py

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional

from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.rest_api_dependencies import get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges
from game_server.config.logging.logging_setup import app_logger as logger

# Импорт моделей
from game_server.common_contracts.api_models.gateway_api import BotAcknowledgementRequest

router = APIRouter(tags=["Command Lifecycle"])

@router.post("/{command_id}/ack", status_code=status.HTTP_200_OK)
async def acknowledge_command(
    command_id: str,
    request_body: Optional[BotAcknowledgementRequest] = None,
    message_bus: IMessageBus = Depends(get_message_bus_dependency)
):
    """
    Эндпоинт для подтверждения ботом выполнения команды.
    Публикует событие подтверждения в RabbitMQ.
    ПРИМЕЧАНИЕ: Этот эндпоинт не инициирует новую команду, а подтверждает
    старую, поэтому его логика отличается от стандартной.
    """
    logger.info(f"Получен ACK-запрос для команды: {command_id}.")

    ack_payload = {
        "command_id": command_id,
        "status": request_body.status if request_body else "success",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "discord_bot_http_ack",
        "details": request_body.error_details if request_body else None
    }
    
    # Ключ для ACK событий может быть более специфичным
    routing_key = f"event.bot.ack.{command_id}"

    try:
        # Публикуем событие подтверждения в общую шину событий
        await message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=routing_key,
            message=ack_payload
        )
        logger.info(f"Команда {command_id} успешно подтверждена (ACK) через RabbitMQ.")
    
    except Exception as e:
        logger.error(f"Ошибка при публикации ACK для команды {command_id} в RabbitMQ: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Внутренняя ошибка при обработке подтверждения."
        )

    return {"status": "acknowledged", "command_id": command_id}

gateway_command_router = router
