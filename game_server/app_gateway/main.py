# /game_server/api_fast/main.py

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI
from dotenv import load_dotenv

# 🔥 НОВЫЕ ИМПОРТЫ для унифицированной архитектуры WS
from game_server.app_gateway.gateway.client_connection_manager import ClientConnectionManager
from game_server.app_gateway.gateway.websocket_outbound_dispatcher import OutboundWebSocketDispatcher

# Импорты конфигурации роутеров
from game_server.app_gateway.rest_routers.routers_config import ROUTERS_CONFIG
from game_server.app_gateway.ws_routers_config import WS_ROUTERS_CONFIG 

from game_server.config.logging.logging_setup import app_logger as logger

# Используем функции из отдельного файла
from game_server.app_gateway.gateway_dependencies import initialize_gateway_dependencies, shutdown_gateway_dependencies
from game_server.config.settings_core import APP_VERSION

root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(root_env)

# Описание тегов для Swagger UI
tags_metadata = [
    {"name": "Gateway REST", "description": "REST API для служебных операций шлюза."},
    {"name": "Unified WebSocket", "description": "Унифицированный WebSocket API для всех типов клиентов (игроки, бот, админ)."}, 
    {"name": "System", "description": "Системные REST API для получения справочных данных и управления."}, 
    {"name": "Authentication", "description": "REST API для аутентификации игроков и системных клиентов."},
    {"name": "Health", "description": "Проверка состояния сервиса."},
]

# 🔥 ИЗМЕНЕНИЕ: Глобальные переменные для новых универсальных менеджеров
global_client_connection_manager: Optional[ClientConnectionManager] = None
# global_system_command_listener: Optional[SystemCommandListener] = None # УДАЛЕНО: Этот слушатель больше не нужен
global_outbound_ws_dispatcher: Optional[OutboundWebSocketDispatcher] = None # Универсальный исходящий диспетчер


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет запуском и остановкой сервисов Gateway.
    """
    logger.info("🚀 Запуск Lifespan шлюза в оптимизированном режиме...")
    
    global global_client_connection_manager
    # global global_system_command_listener # УДАЛЕНО: Этот слушатель больше не нужен
    global global_outbound_ws_dispatcher

    try:
        app.state.gateway_dependencies = await initialize_gateway_dependencies()
        
        if "message_bus" not in app.state.gateway_dependencies or app.state.gateway_dependencies["message_bus"] is None:
            logger.critical("🚨 КРИТИЧЕСКАЯ ОШИБКА: RabbitMQ Message Bus отсутствует или не инициализирован в gateway_dependencies!")
            raise RuntimeError("RabbitMQ Message Bus не инициализирован. Запуск шлюза невозможен.")

        message_bus = app.state.gateway_dependencies['message_bus']
        app.state.message_bus = message_bus 

        # 🔥 ИЗМЕНЕНИЕ: Инициализация универсального ClientConnectionManager
        global_client_connection_manager = ClientConnectionManager()
        app.state.client_connection_manager = global_client_connection_manager # Доступен через app.state
        
        # 🔥 ИЗМЕНЕНИЕ: Инициализация универсального OutboundWebSocketDispatcher
        # Он слушает RabbitMQ и отправляет сообщения всем клиентам
        global_outbound_ws_dispatcher = OutboundWebSocketDispatcher(
            message_bus=message_bus,
            client_connection_manager=global_client_connection_manager # Передаем универсальный менеджер соединений
        )
        app.state.outbound_ws_dispatcher = global_outbound_ws_dispatcher
        
        await global_outbound_ws_dispatcher.start_listening_for_outbound_messages()
        # Сохраняем ссылку на внутреннюю задачу, созданную диспетчером, для ее последующей отмены
        app.state.outbound_ws_dispatcher_task = global_outbound_ws_dispatcher._listen_task

        logger.info("✅ Оптимизированный шлюз готов к работе.")
        
        yield # Контекст Lifespan активен

    finally:
        logger.info("👋 Завершение работы Lifespan шлюза...")


        # Отмена таски OutboundWebSocketDispatcher
        if hasattr(app.state, 'outbound_ws_dispatcher_task') and app.state.outbound_ws_dispatcher_task:
            app.state.outbound_ws_dispatcher_task.cancel()
            try:
                await app.state.outbound_ws_dispatcher_task
            except asyncio.CancelledError:
                pass

        if hasattr(app.state, 'gateway_dependencies'):
            await shutdown_gateway_dependencies(app.state.gateway_dependencies)
        logger.info("✅ Ресурсы шлюза освобождены.")


app = FastAPI(
    title="Optimized Command Gateway API",
    version=APP_VERSION,
    lifespan=lifespan, # Привязываем lifespan
    openapi_tags=tags_metadata
)

# Подключаем REST роутеры
logger.info("Подключение REST роутеров...")
for router_config in ROUTERS_CONFIG:
    app.include_router(
        router_config["router"],
        prefix=router_config.get("prefix", ""),
        tags=router_config.get("tags", [])
    )

# 🔥 ИЗМЕНЕНИЕ: Подключаем WebSocket роутеры (будет только один унифицированный)
logger.info("Подключение WebSocket роутеров...")
for ws_router_config in WS_ROUTERS_CONFIG: 
    app.include_router(
        ws_router_config["router"],
        prefix=ws_router_config.get("prefix", ""),
        tags=ws_router_config.get("tags", [])
    )