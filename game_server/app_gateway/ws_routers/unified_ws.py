# game_server/app_gateway/ws_routers/unified_ws.py

import asyncio
import json
from typing import Optional, Dict, Any
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from starlette.websockets import WebSocketState

from game_server.common_contracts.shared_models.api_contracts import WebSocketMessage, WebSocketResponsePayload, ResponseStatus
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.gateway.client_connection_manager import ClientConnectionManager

from game_server.app_gateway.rest_api_dependencies import get_client_connection_manager_dependency, get_message_bus_dependency
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys, Queues

logger.info("--- 🚀 Загружен унифицированный WebSocket-роутер (unified_ws.py) ---")

router = APIRouter(tags=["Unified WebSocket"])

# Константы для типов клиентов
CLIENT_TYPE_PLAYER = "PLAYER"
CLIENT_TYPE_DISCORD_BOT = "DISCORD_BOT"
CLIENT_TYPE_ADMIN_PANEL = "ADMIN_PANEL"

# ЕДИНСТВЕННЫЙ УНИФИЦИРОВАННЫЙ WebSocket-эндпоинт
@router.websocket("/v1/connect") # Проверьте, что это путь, который использует бот
async def unified_websocket_endpoint(
    websocket: WebSocket,
    client_conn_manager: ClientConnectionManager = Depends(get_client_connection_manager_dependency),
    message_bus: IMessageBus = Depends(get_message_bus_dependency),
):
    """
    Единый эндпоинт для всех WebSocket-соединений.
    Обрабатывает жизненный цикл клиента: аутентификация -> обработка команд -> отключение.
    """
    client_id: Optional[str] = None
    client_type: Optional[str] = None
    client_address = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "N/A"
    
    await websocket.accept()
    logger.info(f"🔌 Входящее соединение от {client_address} принято. Ожидание аутентификации...")

    try:
        # --- ШАГ 1: АУТЕНТИФИКАЦИЯ ---
        auth_payload_str = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_payload = json.loads(auth_payload_str)

        token_to_validate = auth_payload.get("token")
        requested_client_type = auth_payload.get("client_type")
        bot_name_from_payload = auth_payload.get("bot_name")

        if not token_to_validate or not requested_client_type:
            logger.warning(f"❌ Отсутствует токен или тип клиента в аутентификационных данных от {client_address}.")
            raise ValueError("Missing 'token' or 'client_type' in authentication data.")

        rpc_request_data = {
            "token": token_to_validate,
            "client_type": requested_client_type,
            "bot_name": bot_name_from_payload
        }
        
        logger.info(f"Отправка RPC-запроса на валидацию токена для типа клиента: {requested_client_type}...")
        
        validation_result = await message_bus.call_rpc(
            queue_name=Queues.AUTH_VALIDATE_TOKEN_RPC,
            payload=rpc_request_data
        )

        if validation_result and validation_result.get("is_valid"):
            client_id = validation_result.get("client_id")
            client_type = validation_result.get("client_type")
            if not client_id or not client_type:
                logger.warning(f"❌ RPC-ответ не содержит client_id или client_type: {validation_result}")
                raise ValueError("Invalid RPC response: missing client_id or client_type.")
            logger.info(f"✅ Клиент {client_id} ({client_type}) успешно аутентифицирован через RPC.")

            auth_confirm_correlation_id = uuid.uuid4()

            auth_confirm_payload = WebSocketResponsePayload(
                request_id=auth_confirm_correlation_id,
                status=ResponseStatus.SUCCESS,
                message="Authentication successful.",
                data={"client_id": client_id, "client_type": client_type}
            )
            auth_confirm_message = WebSocketMessage(
                type="AUTH_CONFIRM",
                correlation_id=auth_confirm_correlation_id,
                payload=auth_confirm_payload
            )
            await websocket.send_text(auth_confirm_message.model_dump_json())
            logger.info(f"Отправлено подтверждение аутентификации клиенту {client_id}.")

        else:
            error_message = validation_result.get("error", "Неизвестная ошибка валидации токена.")
            logger.warning(f"❌ Аутентификация клиента {client_address} не удалась: {error_message}")
            raise ValueError(f"Authentication failed: {error_message}")

        if not client_id:
            raise ValueError("В аутентификационных данных отсутствует 'client_id' после обработки.")
        
        # --- ШАГ 2: РЕГИСТРАЦИЯ СОЕДИНЕНИЯ ---
        await client_conn_manager.connect(websocket, client_id, client_type)

        # --- ШАГ 3: ОСНОВНОЙ ЦИКЛ ОБРАБОТКИ КОМАНД ---
        while True:
            message_text = await websocket.receive_text()
            raw_message_dict = json.loads(message_text)

            websocket_msg = WebSocketMessage.model_validate(raw_message_dict)

            if websocket_msg.type == "COMMAND":
                command_payload = websocket_msg.payload
                
                # Добавляем client_id на верхний уровень payload,
                # чтобы BaseCommandDTO мог его получить.
                command_payload['client_id'] = client_id

                logger.debug(f"unified_ws: client_id перед публикацией команды: {client_id}")
                logger.debug(f"unified_ws: command_payload перед публикацией: {command_payload}")

                domain = command_payload.get("domain", "system")
                action = command_payload.get("action", "default")
                routing_key = f"{RoutingKeys.COMMAND_PREFIX}.{domain}.{action}"
                
                logger.debug(f"Получена команда от {client_id}. Ключ: '{routing_key}'.")

                await message_bus.publish(
                    exchange_name=Exchanges.COMMANDS,
                    routing_key=routing_key,
                    message=command_payload
                )
                logger.info(f"Команда от {client_id} опубликована в {Exchanges.COMMANDS} с ключом '{routing_key}'.")

            elif websocket_msg.type == "ACK":
                logger.debug(f"Получен ACK от клиента {client_id} для сообщения {websocket_msg.correlation_id}")
            else:
                logger.warning(f"Получено сообщение неизвестного типа '{websocket_msg.type}' от клиента {client_id}.")

    except WebSocketDisconnect:
        logger.info(f"Клиент {client_id or client_address} отключился.")
    except asyncio.TimeoutError:
        logger.warning(f"Таймаут аутентификации для клиента {client_address}. Соединение закрыто.")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication timeout.")
    except Exception as e:
        logger.error(f"Произошла ошибка в WebSocket-соединении для {client_id or client_address}: {e}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error.")
    finally:
        if client_id:
            client_conn_manager.disconnect(client_id)
        logger.info(f"Соединение с {client_id or client_address} полностью закрыто.")
