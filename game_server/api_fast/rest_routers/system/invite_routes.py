# Файл: rest_routers/system/invite_routes.py

from fastapi import APIRouter, Depends
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response
from game_server.api_fast.api_models.system_api import RegisterOrLoginRequest # Используем ту же модель запроса
from game_server.Logic.ApplicationLogic.api_reg.auth_service import AuthService
from game_server.api_fast.dependencies import get_auth_service
from .system_parsers import parse_register_or_login

router = APIRouter(
    prefix="/invite",
    tags=["Game Invites"]
)

@router.post("/request_shard_access")
async def request_shard_access_route(
    request_data: RegisterOrLoginRequest = Depends(parse_register_or_login),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Принимает Discord ID, регистрирует пользователя (если необходимо)
    и возвращает ID шарда, на который нужно сгенерировать инвайт.
    """
    try:
        # Вызываем наш новый "умный" метод
        result = await auth_service.get_shard_for_discord_user(request_data)
        return create_success_response(data=result)
    except Exception as e:
        return create_error_response(code="SHARD_ACCESS_ERROR", message=str(e))
