# api_fast/ws_routers/gateway/gateway_config.py

# Импортируем роутеры из соседних файлов этого же домена
from .gateway_ws import gateway_command_ws_router
# from .другой_ws_файл import другой_ws_роутер # <-- на будущее

# Имя переменной: [имя_папки]_ws_routers

gateway_ws_routers = [
    {
        "router": gateway_command_ws_router,
        "prefix": "/ws", # Этот префикс мы оставили
        "tags": ["Gateway WebSocket"] # <--- ЭТОТ ТЕГ ОБЯЗАТЕЛЕН для отображения в Swagger UI!
    },
]