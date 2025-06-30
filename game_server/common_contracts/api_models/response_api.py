# game_server\common_contracts\api_models\response_api.py

# Удаляем ErrorModel и APIResponse, так как они теперь в shared_models.api_contracts
# from pydantic import BaseModel, Field
from typing import TypeVar, Generic, Optional, Any

from pydantic import BaseModel, Field

from game_server.common_contracts.shared_models.api_contracts import APIResponse, ErrorDetail

# Импортируем стандартизированные модели из нового общего файла


T = TypeVar('T')

# Вспомогательные функции теперь используют модели из api_contracts
def create_success_response(data: T, message: Optional[str] = "Operation successful") -> APIResponse[T]:
    """Создает стандартизированный успешный ответ."""
    return APIResponse(success=True, data=data, message=message)

def create_error_response(code: str, message: str, data: T = None) -> APIResponse[Any]: # data может быть любым типом
    """Создает стандартизированный ответ с ошибкой."""
    return APIResponse(success=False, error=ErrorDetail(code=code, message=message), data=data)


# --- Модели для ОТВЕТОВ от API (если они не являются SuccessResponse) ---
# Эти модели остаются, так как они описывают конкретную структуру данных,
# которая может быть вложена в data поля APIResponse, если роут вернет 200 OK
# Но для 202 Accepted они не нужны как прямые response_model

# Если эти модели используются только для RPC-ответов (например, в discord_get_routes),
# то они могут быть DTO или же использоваться как T в APIResponse[T]
class SessionSuccessResponse(BaseModel): # BaseModel будет импортирована из shared_models.api_contracts
    """
    Модель успешного ответа для Роута №2, содержащая токен сессии.
    (Предполагается, что будет использоваться как 'data' в APIResponse)
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")

class RoutingSuccessResponse(BaseModel): # BaseModel будет импортирована из shared_models.api_contracts
    """
    Модель успешного ответа для Роута №1, содержащая данные для маршрутизации.
    (Предполагается, что будет использоваться как 'data' в APIResponse)
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: str = Field(..., description="ID шарда, на который следует направить игрока.")