# Discord_API\discord_functions\utils\discord_api_helpers.py 

import asyncio
import discord
from Discord_API.config.logging.logging_setup import logger
from Discord_API.discord_settings import  ( # <--- Убедитесь, что путь правильный
    MAX_RETRIES_PER_ROLE,
    INITIAL_SHORT_PAUSE,
    RATE_LIMIT_PAUSE,
    CREATION_TIMEOUT,
    MAX_RETRY_SLEEP
)


async def execute_discord_api_call(api_call_factory_func, *, description="API call", timeout=CREATION_TIMEOUT, retries=MAX_RETRIES_PER_ROLE):
    """
    Выполняет асинхронный вызов Discord API с логикой повторных попыток,
    обработкой таймаутов и рейт-лимитов.
    Возвращает (результат_вызова, True/False - был ли рейт-лимит/таймаут в этой попытке).
    """
    encountered_problem = False # Флаг, который будет True, если был таймаут или 429
    for attempt in range(retries):
        try:
            logger.debug(f"DEBUG: Попытка {attempt + 1}/{retries} выполнения '{description}' с таймаутом {timeout}с.")
            result = await asyncio.wait_for(api_call_factory_func(), timeout=timeout)
            logger.debug(f"DEBUG: Успешно выполнено: '{description}'.")
            return result, encountered_problem # Возвращаем результат и флаг
        except asyncio.TimeoutError:
            logger.error(f"❌ ПРОБЛЕМА: Таймаут ({timeout}с) при '{description}'. Discord API не ответил. Новая попытка ({attempt + 1}/{retries}).")
            encountered_problem = True # Была проблема
            if attempt < retries - 1:
                await asyncio.sleep(MAX_RETRY_SLEEP)
            else:
                raise
        except discord.Forbidden:
            logger.error(f"❌ ОШИБКА: Недостаточно прав для '{description}'. Пропускаем.", exc_info=True)
            encountered_problem = True # Была проблема
            raise
        except discord.HTTPException as e:
            if e.status == 429: # Рейт-лимит
                retry_after = min(int(e.response.headers.get("Retry-After", RATE_LIMIT_PAUSE)), MAX_RETRY_SLEEP)
                logger.warning(f"⚠️ ПРОБЛЕМА: Рейт-лимит Discord API при '{description}'. Задержка {retry_after} сек. Новая попытка ({attempt + 1}/{retries}).")
                encountered_problem = True # Была проблема
                await asyncio.sleep(retry_after)
            else:
                logger.error(f"❌ ПРОБЛЕМА: ОШИБКА API при '{description}': Статус: {e.status}, Текст: {e.text}. Новая попытка ({attempt + 1}/{retries}).", exc_info=True)
                encountered_problem = True # Была проблема
                if attempt < retries - 1:
                    await asyncio.sleep(RATE_LIMIT_PAUSE)
                else:
                    raise
        except Exception as e:
            logger.error(f"❌ ПРОБЛЕМА: Непредвиденная ошибка при '{description}': {e}. Новая попытка ({attempt + 1}/{retries}).", exc_info=True)
            encountered_problem = True # Была проблема
            if attempt < retries - 1:
                await asyncio.sleep(RATE_LIMIT_PAUSE)
            else:
                raise

    # Если выполнение дошло сюда, значит, все попытки исчерпаны, и было выброшено исключение.
    # Но если каким-то образом исключение не было выброшено, то все равно возвращаем флаг.
    raise Exception(f"Не удалось выполнить '{description}' после {retries} попыток.")

def is_name_conflict_error(e: discord.HTTPException) -> bool:
    """
    Проверяет, является ли HTTPException ошибкой конфликта имени (400 Bad Request с specific_code 50035).
    Эта ошибка часто возникает при создании ролей, каналов или категорий с уже существующим именем.
    """
    # Discord API возвращает 400 Bad Request с кодом 50035 (Invalid Form Body/Value)
    # когда имя ресурса уже существует. Текст ошибки также часто содержит "already exists".
    return e.status == 400 and (e.code == 50035 or "already exists" in e.text.lower())


def is_invalid_parameter_error(e: discord.HTTPException) -> bool:
    """
    Проверяет, является ли HTTPException ошибкой неверных параметров (400 Bad Request, часто с code 50035).
    Может возникать из-за слишком длинного имени, недопустимых символов и т.п.
    """
    # Ошибка 50035 - "Invalid Form Body" или "Invalid Form Values"
    return e.status == 400 and e.code == 50035

def is_guild_channel_limit_exceeded_error(e: discord.HTTPException) -> bool:
    """
    Проверяет, является ли HTTPException ошибкой превышения лимита каналов/категорий в гильдии.
    Discord не имеет специфического публичного кода ошибки для этого.
    Это часто будет 50035 "Invalid Form Body" или 500 "Internal Server Error"
    с сообщением, указывающим на лимит. В документации API для "Create Guild Channel"
    упоминается 50035 для "Maximum number of channels reached".
    """
    # Discord API 50035 "Maximum number of channels reached (500)"
    return e.status == 400 and (e.code == 50035 and "maximum number of channels reached" in e.text.lower())

# Возможно, более общая функция, если текст ошибки меняется
def is_guild_limit_exceeded(e: discord.HTTPException, limit_type: str) -> bool:
    """
    Проверяет, является ли HTTPException ошибкой превышения общего лимита в гильдии.
    limit_type может быть "channels", "roles" и т.п.
    """
    return (e.status == 400 and e.code == 50035 and f"maximum number of {limit_type} reached" in e.text.lower())
