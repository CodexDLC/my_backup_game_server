# rest_routers/character/character_config.py
from .creation import character_creation_router
from .auto_session import auto_session_router

character_routers = [
    {
        "router": character_creation_router,
        "prefix": "/character",
        "tags": ["Character"],
    },
    {
        "router": auto_session_router,
        "prefix": "/character/auto_session",
        "tags": ["Character", "Testing"],
    }
]