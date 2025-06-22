# rest_routers/character/character_parsers.py
from fastapi import Request
from game_server.api_fast.api_models.character_api import CharacterCreateRequest, AutoSessionRequest

async def parse_character_creation(request: Request) -> CharacterCreateRequest:
    """Парсит JSON-запрос на создание персонажа."""
    return CharacterCreateRequest(**await request.json())

async def parse_auto_session(request: Request) -> AutoSessionRequest:
    """Парсит JSON-запрос на управление авто-сессией."""
    return AutoSessionRequest(**await request.json())