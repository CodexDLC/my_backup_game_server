# discord_bot/command_client.py
import asyncio
import json
import websockets
import aiohttp # Используем aiohttp для HTTP-запросов
from typing import TYPE_CHECKING # Для тайп-хинтинга, чтобы избежать циклических импортов

# Используем ваш глобальный логгер и настройки Discord
from Discord_API.config.logging.logging_setup_discod import logger
from Discord_API.discord_settings import GATEWAY_AUTH_TOKEN, GATEWAY_URL

# Импорт класса Bot для тайп-хинтинга (для 'self.bot' в __init__)
if TYPE_CHECKING:
    from discord.ext.commands import Bot as DiscordBot # Или discord.Client, если не используете commands.Bot

# --- Конфигурация клиента ---
# Проверка наличия обязательных переменных окружения
if not GATEWAY_URL or not GATEWAY_AUTH_TOKEN:
    # Предполагается, что GATEWAY_AUTH_TOKEN - это ваш GATEWAY_BOT_SECRET на стороне бота
    raise ValueError("Переменные окружения GATEWAY_URL и GATEWAY_AUTH_TOKEN должны быть установлены для бота!")

# Импорт реестра обработчиков команд
from Discord_API.core.command_handlers.registry import COMMAND_HANDLERS

class BotCommandClient:
    """
    Клиент для взаимодействия Discord-бота с центральным шлюзом через WebSocket
    для получения команд и через REST API для отправки подтверждений.
    """
    def __init__(self, bot: 'DiscordBot'):
        """
        Инициализирует BotCommandClient.
        :param bot: Экземпляр discord.ext.commands.Bot или discord.Client.
        """
        self.bot = bot
        self.websocket = None
        self.gateway_url = GATEWAY_URL
        self.auth_token = GATEWAY_AUTH_TOKEN
        self.is_running = True # Флаг для управления циклом listen_for_commands
        self.http_session = None # Сессия aiohttp для переиспользования
        logger.info(f"✅ BotCommandClient инициализирован. Шлюз: {self.gateway_url}")

    async def _get_http_session(self):
        """Возвращает или создает aiohttp ClientSession."""
        if self.http_session is None or self.http_session.closed:
            self.http_session = aiohttp.ClientSession()
            logger.debug("Создана новая aiohttp.ClientSession.")
        return self.http_session

    async def connect(self) -> bool:
        try:
            logger.info(f"Подключение к WebSocket шлюзу: {self.gateway_url}...")
            
            ws_url = self.gateway_url.replace('http://', 'ws://').replace('https://', 'wss://')
            if not (ws_url.startswith('ws://') or ws_url.startswith('wss://')):
                 ws_url = f"ws://{ws_url}"
            
            # --- ДОБАВЬТЕ ЭТУ СТРОКУ ДЛЯ ОТЛАДКИ: ---
            final_ws_connect_url = f"{ws_url}/ws/bot/commands"
            logger.info(f"⚡️ Попытка WebSocket подключения к: {final_ws_connect_url}")
            # ----------------------------------------
            self.websocket = await websockets.connect(final_ws_connect_url)
            await self.websocket.send(self.auth_token) # Отправляем токен для аутентификации
            logger.info("Успешно подключен к WebSocket шлюзу и отправлен токен аутентификации.")
            return True
        except Exception as e:
            logger.error(f"Не удалось подключиться к WebSocket шлюзу: {e}", exc_info=True)
            self.websocket = None
            return False

    async def listen_for_commands(self):
        """
        Главный асинхронный цикл для прослушивания команд из WebSocket.
        Пытается переподключиться при потере соединения.
        """
        # Инициализируем HTTP-сессию при старте прослушивания
        await self._get_http_session()

        while self.is_running:
            if not self.websocket or self.websocket.closed:
                logger.warning("WebSocket соединение не активно или закрыто. Попытка переподключения через 5с...")
                if not await self.connect():
                    await asyncio.sleep(5) # Если переподключение не удалось, ждем перед повторной попыткой
                    continue # Пропускаем остаток цикла и пробуем снова

            try:
                message = await self.websocket.recv()
                command = json.loads(message)
                logger.debug(f"Получена команда через WebSocket: {command.get('command_id')}")
                # Обработка команды должна быть неблокирующей, поэтому запускаем ее как отдельную задачу
                asyncio.create_task(self.handle_command(command))
            except websockets.exceptions.ConnectionClosedOK:
                logger.info("WebSocket соединение закрыто нормально.")
                self.websocket = None
                if self.is_running: # Если бот все еще должен работать, попробуем переподключиться
                    await asyncio.sleep(1) # Небольшая задержка перед переподключением
            except websockets.exceptions.ConnectionClosedError as e:
                logger.error(f"WebSocket соединение закрыто с ошибкой: {e}")
                self.websocket = None
                if self.is_running: # Если бот все еще должен работать, попробуем переподключиться
                    await asyncio.sleep(5) # Большая задержка при ошибке
            except asyncio.CancelledError:
                logger.info("Задача listen_for_commands отменена.")
                break # Выход из цикла при отмене задачи (например, при остановке бота)
            except Exception as e:
                logger.error(f"Ошибка получения/обработки сообщения WebSocket: {e}", exc_info=True)
                self.websocket = None # Сбрасываем соединение при любой другой ошибке
                if self.is_running:
                    await asyncio.sleep(5) # Ждем перед следующей попыткой

    async def handle_command(self, command: dict):
        """
        Умный диспетчер. Находит нужный обработчик в реестре и вызывает его.
        """
        command_id = command.get("command_id")
        command_type = command.get("type")
        
        if not command_id or not command_type:
            logger.error(f"Получена некорректная команда: {command}")
            return

        # Находим нужный обработчик в нашем словаре COMMAND_HANDLERS
        handler_func = COMMAND_HANDLERS.get(command_type)

        if handler_func:
            logger.info(f"Найден обработчик для команды '{command_type}'. Запуск...")
            try:
                # Вызываем найденный обработчик, передавая ему бота и полезную нагрузку
                await handler_func(self.bot, command.get("payload", {}))
                
                # Если все прошло без ошибок, отправляем ACK (подтверждение)
                await self.ack_command(command_id)

            except Exception as e:
                logger.error(f"Ошибка выполнения обработчика для команды {command_id} ({command_type}): {e}", exc_info=True)
                # TODO: Логика для отправки NACK (negative acknowledgment) - сообщить шлюзу об ошибке
        else:
            logger.warning(f"Обработчик для команды типа '{command_type}' не найден/не зарегистрирован.")

    async def ack_command(self, command_id: str):
        """
        Отправляет подтверждение выполнения команды через REST API с использованием aiohttp.
        """
        # GATEWAY_URL, который вы используете, это http://fast_api:8000/ws
        # Для ACK нам нужен базовый адрес http://fast_api:8000
        # base_api_url = self.gateway_url.replace('/ws', '')
        # Предполагаем, что GAME_SERVER_API уже настроен в discord_settings для REST
        ack_url = f"{self.gateway_url.replace('/ws', '')}/command_ack" # Пример: http://fast_api:8000/command_ack

        payload = {"command_id": command_id, "status": "success"}
        
        try:
            session = await self._get_http_session()
            async with session.post(ack_url, json=payload) as response:
                response.raise_for_status() # Вызовет исключение для HTTP ошибок (4xx/5xx)
                logger.info(f"ACK для команды {command_id} успешно отправлен на {ack_url}.")
        except aiohttp.ClientResponseError as e:
            logger.error(f"Ошибка HTTP при отправке ACK для {command_id}: {e.status} - {e.message}", exc_info=True)
        except aiohttp.ClientConnectorError as e:
            logger.error(f"Ошибка соединения при отправке ACK для {command_id}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Неизвестная ошибка при отправке ACK для {command_id}: {e}", exc_info=True)

    async def stop(self):
        """
        Корректно закрывает WebSocket-соединение и останавливает цикл прослушивания.
        Закрывает также HTTP-сессию aiohttp.
        """
        logger.info("Получен сигнал на остановку BotCommandClient.")
        self.is_running = False # Устанавливаем флаг для выхода из цикла listen_for_commands

        if self.websocket and not self.websocket.closed:
            logger.info("Закрытие WebSocket соединения BotCommandClient...")
            await self.websocket.close()
            self.websocket = None

        if self.http_session and not self.http_session.closed:
            logger.info("Закрытие aiohttp.ClientSession...")
            await self.http_session.close()
            self.http_session = None
            
        logger.info("BotCommandClient остановлен.")