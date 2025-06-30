# game_server/app_gateway/rest_api_dependencies.py

from fastapi import Depends, Request, WebSocket # <-- Убедитесь, что WebSocket тоже импортирован
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.app_gateway.gateway.client_connection_manager import ClientConnectionManager

def get_message_bus_dependency(request: Request = None, websocket: WebSocket = None) -> IMessageBus:
    """
    FastAPI Dependency: Возвращает инициализированный MessageBus из состояния приложения.
    Может принимать Request или WebSocket.
    """
    app_state_source = request.app.state if request else websocket.app.state
    if not hasattr(app_state_source, 'message_bus') or app_state_source.message_bus is None:
        raise RuntimeError("MessageBus не инициализирован в состоянии приложения.")
    return app_state_source.message_bus

# 🔥 ИЗМЕНЕНИЕ: Функция-зависимость для ClientConnectionManager
# Для WebSocket-зависимостей лучше использовать "websocket: WebSocket"
def get_client_connection_manager_dependency(websocket: WebSocket) -> ClientConnectionManager: # <-- ИЗМЕНЕНО
    """
    FastAPI Dependency: Возвращает инициализированный ClientConnectionManager из состояния приложения.
    """
    if not hasattr(websocket.app.state, 'client_connection_manager') or websocket.app.state.client_connection_manager is None: # <-- ИЗМЕНЕНО
        raise RuntimeError("ClientConnectionManager не инициализирован в состоянии приложения.")
    return websocket.app.state.client_connection_manager