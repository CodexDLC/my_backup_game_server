# api_fast/ws_routers_config.py

# Импортируем локальные списки из каждого домена
from .ws_routers.gateway.gateway_config import gateway_ws_routers
# from .ws_routers.другой_домен.другой_конфиг import ... # <-- на будущее

# Добавляем наш список в общую сумму
WS_ROUTERS_CONFIG = (
    gateway_ws_routers 
    # + другой_список ...
)