# game_server\common_contracts\api_models\gateway_api.py


from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
# BaseModel и Field теперь импортируем из shared_models.api_contracts



# BotAcknowledgementRequest становится избыточной, если мы используем WebSocketAck
# Но если этот эндпоинт используется для HTTP ACK (а не WS ACK),
# то он должен принять correlation_id от бота в теле.
# Если это HTTP ACK, то лучше, чтобы он принимал correlation_id явно.

# Если это HTTP ACK для команд, отправленных через REST API,
# и бот отправляет сюда ACK по HTTP, то это должно выглядеть так:
class BotAcknowledgementRequest(BaseModel): # Наследовать от BaseRequest не обязательно, если это просто ACK для уже полученной команды.
    """
    Модель для тела запроса ACK от бота, отправляемого по HTTP.
    Должен содержать command_id/correlation_id команды, которую он подтверждает.
    """
    command_id: str = Field(..., description="ID команды, которую бот подтверждает.")
    status: str = Field(..., description="Статус выполнения команды (success, failed).")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки, если статус 'failed'.")

# Если этот эндпоинт (/command_id/ack) является HTTP-интерфейсом для получения ACK
# от бота, то BotAcknowledgementRequest нужен.
# Если же ACK'и должны приходить ТОЛЬКО через WebSocket, то этот файл
# может быть значительно упрощен, или даже удален, а вся логика ACK
# будет в WebSocketAck и WebSocket-диспетчере.
# Пока оставляю BotAcknowledgementRequest, но нужно четко понимать его роль:
# это HTTP-ACK от бота на какую-то команду, полученную ботом ранее, или это WS-ACK?
# Судя по старому коду command_routes.py, это HTTP POST для ACK.
# В будущем, возможно, стоит заменить на использование WebSocketAck по WebSocket.