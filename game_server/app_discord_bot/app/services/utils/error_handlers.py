# app/services/utils/error_handlers.py
import functools
import discord
from typing import Callable, Any

from game_server.config.logging.logging_setup import app_logger as logger

def handle_flow_errors(func: Callable) -> Callable:
    """
    Декоратор для асинхронных флоу, который обеспечивает единую обработку ошибок.
    Он оборачивает выполнение функции в try...except блок.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        interaction: discord.Interaction | None = None
        
        # Пытаемся найти interaction в аргументах
        # Сначала в kwargs
        if 'interaction' in kwargs and isinstance(kwargs['interaction'], discord.Interaction):
            interaction = kwargs['interaction']
        # Затем в args
        else:
            for arg in args:
                if isinstance(arg, discord.Interaction):
                    interaction = arg
                    break
        
        try:
            # Выполняем основную логику флоу
            return await func(*args, **kwargs)
        except Exception as e:
            # Логируем критическую ошибку
            logger.critical(f"Критическая ошибка во флоу '{func.__name__}': {e}", exc_info=True)
            
            # Если удалось найти interaction, пытаемся отправить сообщение
            if interaction:
                try:
                    error_message = "❌ Что-то пошло не так в обработке. Пожалуйста, повторите позже или обратитесь к администрации."
                    if not interaction.response.is_done():
                        # Если на interaction еще не отвечали, нужен defer или response
                        await interaction.response.send_message(error_message, ephemeral=True)
                    else:
                        await interaction.followup.send(error_message, ephemeral=True)
                except discord.HTTPException as http_exc:
                    logger.warning(f"Не удалось отправить сообщение об ошибке пользователю {interaction.user.id}: {http_exc}")
            else:
                logger.error(f"Не удалось найти объект Interaction во флоу '{func.__name__}' для отправки сообщения об ошибке.")
    
    return wrapper