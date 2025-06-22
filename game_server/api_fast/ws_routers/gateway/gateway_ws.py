# api_fast/ws_routers/gateway_ws.py

import asyncio
from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from fastapi.responses import HTMLResponse # Для фиктивного GET-эндпоинта

# Используем наш глобальный логгер
from game_server.api_fast.dependencies import get_connection_manager
from game_server.api_fast.gateway.auth import validate_bot_token
from game_server.api_fast.gateway.connection_manager import ConnectionManager

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

router = APIRouter(
    # prefix здесь не нужен, он будет добавлен через WS_ROUTERS_CONFIG
    tags=["Gateway WebSocket"] # Теги оставить для отображения группы в UI
)

@router.get(
    "/bot/commands/docs", # <--- Новый путь для документации
    include_in_schema=True,
    summary="WebSocket endpoint for bot commands (Documentation)",
    description="""
    Это HTTP-эндпоинт для целей документации.
    Для реального подключения используйте **WebSocket** протокол по адресу:
    `ws://ВАШ_ХОСТ:ВАШ_ПОРТ/ws/bot/commands`
    Первое сообщение после подключения должно быть токеном аутентификации.
    """,
    response_class=HTMLResponse
)
async def bot_command_websocket_docs():
    """
    Этот эндпоинт служит исключительно для отображения информации о WebSocket API в Swagger UI.
    """
    return """
    <h1>WebSocket Endpoint for Discord Bot Commands</h1>
    <p>This is a WebSocket endpoint for real-time command delivery to the Discord bot.</p>
    <p><strong>To connect, use a WebSocket client (e.g., in JavaScript or Python) with the URL:</strong></p>
    <code>ws://YOUR_FASTAPI_HOST:8000/ws/bot/commands</code>
    <p>The very first message sent after connection must be your authentication token.</p>
    <p>This page is for documentation purposes only. No HTTP requests can be made here for command delivery.</p>
    """


@router.websocket("/bot/commands")
async def bot_command_websocket(
    websocket: WebSocket,
    connection_manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    Основной WebSocket-эндпоинт для подключения Discord-бота.
    1. Принимает соединение.
    2. Ожидает токен для аутентификации.
    3. Регистрирует соединение в ConnectionManager.
    4. Удерживает соединение активным, пока бот не отключится.
    """
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Возвращаем accept() сюда ---
    await websocket.accept() # <--- ЭТО ВАЖНО: Принять соединение ДО ЛЮБЫХ ОПЕРАЦИЙ receive/send
    logger.info("Попытка подключения нового клиента к WebSocket шлюзу (соединение принято)...")

    try:
        # --- Шаг 1: Аутентификация ---
        token = await asyncio.wait_for(websocket.receive_text(), timeout=10) # Теперь receive_text() сработает
        
        if not await validate_bot_token(token):
            logger.warning(f"Неудачная попытка аутентификации WebSocket с токеном: {token[:10]}...")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        logger.info("Аутентификация бота на WebSocket шлюзе прошла успешно.")
        
        # --- Шаг 2: Регистрация соединения ---
        # Теперь connection_manager.connect() просто добавляет уже принятое соединение
        await connection_manager.connect(websocket) 

        # --- Шаг 3: Цикл удержания соединения ---
        while True:
            message = await websocket.receive_text()
            logger.debug(f"Получено сообщение от бота через WebSocket (keep-alive/pong): {message[:50]}...")

    except WebSocketDisconnect:
        logger.info("Бот отключился от WebSocket шлюза.")
    except asyncio.TimeoutError:
        logger.warning("Клиент не прислал токен аутентификации вовремя. Соединение закрыто.")
        await websocket.close(code=4008, reason="Authentication timeout")
    except Exception as e:
        logger.error(f"Произошла ошибка в WebSocket соединении с ботом: {e}", exc_info=True)
    finally:
        connection_manager.disconnect(websocket) 

# ДОБАВЛЕНО: Статусный эндпоинт для мониторинга
@router.get(
    "/bot/connections/status",
    response_model=dict, # Возвращает словарь с количеством подключений
    summary="WebSocket connections status",
    description="Получить текущий статус активных WebSocket соединений с ботом.",
    tags=["Gateway WebSocket"] # Группируем с другими WebSocket-связанными эндпоинтами
)
async def websocket_status(
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    Возвращает информацию о количестве активных WebSocket соединений.
    """
    return manager.status


gateway_command_ws_router = router