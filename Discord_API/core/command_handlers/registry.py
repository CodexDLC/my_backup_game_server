# discord_bot/command_handlers/registry.py
from typing import Dict, Callable, Awaitable

# 1. Наш центральный реестр: словарь, где ключ - это тип команды,
#    а значение - функция-обработчик.
COMMAND_HANDLERS: Dict[str, Callable[..., Awaitable[None]]] = {}

def register_handler(command_type: str):
    """
    Декоратор, который регистрирует функцию как обработчик
    для определенного типа команды.
    """
    def decorator(handler_func: Callable[..., Awaitable[None]]):
        if command_type in COMMAND_HANDLERS:
            # Предотвращаем случайную перезапись обработчиков
            raise ValueError(f"Обработчик для команды '{command_type}' уже зарегистрирован!")
        COMMAND_HANDLERS[command_type] = handler_func
        return handler_func
    return decorator