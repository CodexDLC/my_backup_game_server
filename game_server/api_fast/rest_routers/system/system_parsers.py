# rest_routers/system/system_parsers.py
from fastapi import Request
from game_server.api_fast.api_models.system_api import RegisterOrLoginRequest

async def parse_register_or_login(request: Request) -> RegisterOrLoginRequest:
    """Парсит JSON-запрос на регистрацию/логин."""
    return RegisterOrLoginRequest(**await request.json())