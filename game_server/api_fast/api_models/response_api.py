# game_server/api_fast/api_models/response_api.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class ErrorModel(BaseModel):
    """Стандартная модель для описания ошибки."""
    code: str
    message: str

class APIResponse(BaseModel, Generic[T]):
    """
    Универсальная модель-обертка для всех ответов API.
    Используется во всех роутах в `response_model`.
    """
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorModel] = None
    message: Optional[str] = None # <-- ДОБАВЛЕНО: Поле для сообщения

# Вспомогательные функции для удобного создания ответов
def create_success_response(data: T, message: Optional[str] = "Operation successful") -> APIResponse[T]: # <-- ДОБАВЛЕНО: message
    """Создает стандартизированный успешный ответ."""
    return APIResponse(data=data, success=True, message=message) # <-- ДОБАВЛЕНО: message и success=True

def create_error_response(code: str, message: str, data: T = None) -> APIResponse: # <-- ДОБАВЛЕНО: data для ошибок
    """Создает стандартизированный ответ с ошибкой."""
    return APIResponse(success=False, error=ErrorModel(code=code, message=message), data=data) # <-- ДОБАВЛЕНО: data и errorModel