# api_fast/rest_routers/gateway/gateway_config.py

# Импортируем роутеры из соседних файлов этого же домена
from .command_routes import gateway_command_router
# from .другой_файл import другой_роутер # <-- на будущее

# Имя переменной: [имя_папки]_routers

gateway_routers = [
    {
        "router": gateway_command_router,
        "prefix": "/gateway/commands", # <-- префикс для всех роутов этого файла
        "tags": ["Gateway REST"],
    },
    
]

