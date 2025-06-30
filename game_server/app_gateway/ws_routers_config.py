# api_fast/ws_routers_config.py

# 🔥 ИЗМЕНЕНИЕ: Импортируем только новый унифицированный WebSocket-роутер
from .ws_routers.unified_ws import router as unified_websocket_router # ИМПОРТИРУЕМ 'router' и даем ему псевдоним 'unified_websocket_router'

# Добавляем наш список в общую сумму
WS_ROUTERS_CONFIG = (
    [
        {
            "router": unified_websocket_router, # Теперь это имя корректно ссылается на импортированный роутер            
            "tags": ["Unified WebSocket"] # Новый тег для Swagger UI
        },
    ]
)