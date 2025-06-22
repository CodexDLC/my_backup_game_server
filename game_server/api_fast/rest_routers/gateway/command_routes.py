# api_fast/rest_routers/gateway/command_routes.py

from fastapi import APIRouter, Depends, HTTPException, status

from game_server.api_fast.dependencies import get_redis_client
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient


from ...gateway.gateway_config import GATEWAY_LISTEN_STREAMS, GATEWAY_CONSUMER_GROUP_NAME

# Создаем экземпляр роутера, который будем экспортировать
router = APIRouter()

@router.post("/{command_id}/ack", status_code=status.HTTP_200_OK)
async def acknowledge_command(
    command_id: str,
    redis: CentralRedisClient = Depends(get_redis_client)
):
    """
    Эндпоинт для подтверждения ботом выполнения команды.
    Получает ID команды и выполняет XACK в Redis.
    """
    if not redis.redis:
        logger.critical("ACK Endpoint: Redis не инициализирован!")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Сервис временно недоступен (Redis)")

    acknowledged_in_stream = None
    try:
        # TODO: В будущем, если стримов станет много, потребуется более умный механизм,
        # чтобы знать, в каком именно стриме подтверждать команду.
        for stream_name in GATEWAY_LISTEN_STREAMS:
            acked_count = await redis.redis.xack(stream_name, GATEWAY_CONSUMER_GROUP_NAME, command_id)
            if acked_count > 0:
                acknowledged_in_stream = stream_name
                logger.debug(f"Команда {command_id} успешно подтверждена (ACK) в стриме {stream_name}.")
                break
        
        if not acknowledged_in_stream:
            logger.warning(f"Получен ACK для команды {command_id}, но она не найдена в ожидающих обработки.")
    
    except Exception as e:
        logger.error(f"Ошибка при подтверждении (ACK) команды {command_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутренняя ошибка при обработке подтверждения.")

    return {"status": "acknowledged", "command_id": command_id, "stream": acknowledged_in_stream}

# Экспортируем роутер для использования в локальном конфиге
gateway_command_router = router