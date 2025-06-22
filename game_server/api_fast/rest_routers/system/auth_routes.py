# rest_routers/system/auth_routes.py
from fastapi import APIRouter, Depends, Request
from game_server.api_fast.api_models.response_api import APIResponse, create_success_response, create_error_response
from game_server.api_fast.api_models.system_api import RegisterOrLoginRequest, AuthData, PlayerData, LinkingUrlData

from game_server.Logic.ApplicationLogic.api_reg.auth_service import AuthService
from game_server.api_fast.dependencies import get_auth_service # Предполагаем, что есть get_auth_service
from .system_parsers import parse_register_or_login

router = APIRouter()

# Вспомогательная зависимость для токена, которую можно вынести в dependencies.py
async def get_auth_token(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Эта ошибка будет поймана в except блоке
        raise ValueError("Не предоставлен Bearer токен аутентификации.")
    return auth_header.split(" ")[1]

@router.post("/register_or_login", response_model=APIResponse[AuthData])
async def register_or_login_platform(
    request_data: RegisterOrLoginRequest = Depends(parse_register_or_login),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        result = await auth_service.create_or_link_account(request_data)
        return create_success_response(data=result)
    except ValueError as e:
        return create_error_response(code="AUTH_ERROR", message=str(e))
    except Exception as e:
        return create_error_response(code="INTERNAL_SERVER_ERROR", message=str(e))

@router.get("/player_data", response_model=APIResponse[PlayerData])
async def get_player_data_route(
    auth_token: str = Depends(get_auth_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        player_data = await auth_service.get_player_full_data(auth_token)
        return create_success_response(data=player_data)
    except ValueError as e: # Если токен невалиден, сервис вернет ошибку
        return create_error_response(code="UNAUTHORIZED", message=str(e))
    except Exception as e:
        return create_error_response(code="INTERNAL_SERVER_ERROR", message=str(e))

@router.get("/generate_linking_url", response_model=APIResponse[LinkingUrlData])
async def generate_linking_url_route(
    auth_token: str = Depends(get_auth_token),
    auth_service: AuthService = Depends(get_auth_service)
):
    try:
        result = await auth_service.generate_linking_url(auth_token)
        return create_success_response(data=result)
    except ValueError as e:
        return create_error_response(code="UNAUTHORIZED", message=str(e))
    except Exception as e:
        return create_error_response(code="INTERNAL_SERVER_ERROR", message=str(e))

auth_routes_router = router