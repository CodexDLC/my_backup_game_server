# rest_routers/utils_route/utils_config.py
from .import_yami import import_yami_route

# Используем имя папки для переменной
utils_routers = [
    {
        "router": import_yami_route,
        "prefix": "/utils",
        "tags": ["Utilities"],
    }
]