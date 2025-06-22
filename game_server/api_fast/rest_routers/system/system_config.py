# rest_routers/system/system_config.py
from .auth_routes import auth_routes_router
from .system_mapping import system_mapping_router # было system_mapping_route

system_routers = [
    {
        "router": auth_routes_router,
        "prefix": "/auth",
        "tags": ["System"],
    },
    {
       "router": system_mapping_router,
       "prefix": "/mapping",
       "tags": ["System"],
    }
]