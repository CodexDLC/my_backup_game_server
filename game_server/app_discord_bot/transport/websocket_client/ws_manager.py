# game_server/app_discord_bot/transport/websocket_client/ws_manager.py

import aiohttp
import asyncio
import uuid
import json
import logging
from typing import Any, Dict, Optional, Tuple
from discord.ext import commands
import aiohttp.client_exceptions

from game_server.app_discord_bot.transport.websocket_client.handlers.event_handlers import WSEventHandlers
from game_server.app_discord_bot.transport.websocket_client.handlers.system_command_handlers import WSSystemCommandHandlers
from game_server.app_discord_bot.transport.websocket_client.rest_api.websocket_rest_helpers import request_auth_token
from game_server.contracts.shared_models.websocket_base_models import WebSocketCommandFromClientPayload, WebSocketMessage

# Импортируем функции из наших хелпер-файлов
from .websocket_error_handlers import (
    handle_auth_success,
    handle_auth_error_response,
    handle_auth_invalid_data,
    handle_json_decode_error,
    handle_non_text_message,
    handle_client_connector_error,
    handle_timeout_error
)

# 🔥 НОВЫЙ ИМПОРТ ДИСПЕТЧЕРА:
from .websocket_inbound_dispatcher import WebSocketInboundDispatcher




from game_server.app_discord_bot.config.discord_settings import BOT_NAME_FOR_GATEWAY, GATEWAY_AUTH_TOKEN, GATEWAY_URL, GAME_SERVER_API
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache

import inject

# ... (определения Prometheus метрик, если они раскомментированы)


class WebSocketManager:

    @inject.autoparams()
    def __init__(
        self,
        bot: commands.Bot,
        pending_requests_manager: PendingRequestsManager,
        event_handler: WSEventHandlers,
        system_command_handler: WSSystemCommandHandlers,
        logger: logging.Logger,
        bot_cache: Optional[BotCache] = None
    ):
        self.logger = logger
        self.logger.info("WSManager: Начинается инициализация __init__.")
        self.logger.debug("DEBUG: Инициализация WSManager запущена.")

        self._bot = bot
        self._ws_url = GATEWAY_URL
        self._api_key = GATEWAY_AUTH_TOKEN
        self._rest_api_base_url = GAME_SERVER_API
        self._auth_token_rest_endpoint = f"{self._rest_api_base_url}/auth/token"

        if not self._ws_url:
            self.logger.critical("CRITICAL: GATEWAY_URL не установлен.")
            raise ValueError("GATEWAY_URL не установлен в настройках!")
        if not self._api_key:
            self.logger.critical("CRITICAL: GATEWAY_AUTH_TOKEN не установлен.")
            raise ValueError("GATEWAY_AUTH_TOKEN не установлен в настройках!")
        if not self._rest_api_base_url:
            self.logger.critical("CRITICAL: GAME_SERVER_API не установлен.")
            raise ValueError("GAME_SERVER_API не установлен в настройках!")

        self.pending_requests = pending_requests_manager
        self.event_handler = event_handler
        self.system_command_handler = system_command_handler
        self._bot_cache = bot_cache
        self._bot_name = BOT_NAME_FOR_GATEWAY
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._is_running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._websocket_auth_token: Optional[str] = None
        
        # 🔥 Инициализируем наш новый диспетчер
        self._inbound_dispatcher = WebSocketInboundDispatcher(
            logger=self.logger,
            pending_requests_manager=self.pending_requests,
            event_handler=self.event_handler,
            system_command_handler=self.system_command_handler
        )

        self.logger.info("WSManager: Инициализация __init__ завершена.")
        self.logger.debug("DEBUG: Инициализация WSManager завершена успешно.")

    def start(self):
        self.logger.info("WSManager: Вызван метод start().")
        self.logger.debug("DEBUG: Проверка состояния запуска WSManager.")
        if not self._is_running:
            self._is_running = True
            try:
                self._listen_task = asyncio.create_task(
                    self._main_loop(),
                    name=f"WSManager_{self._bot_name}"
                )
                self.logger.info("WSManager: Задача _main_loop создана и запущена.")
                self.logger.debug(f"DEBUG: Задача _main_loop '{self._listen_task.get_name()}' запущена.")
            except Exception as e:
                self.logger.critical(f"Ошибка при создании задачи: {e}", exc_info=True)
                self._is_running = False
        else:
            self.logger.warning("WSManager: Попытка запустить уже запущенный менеджер.")
            self.logger.debug("DEBUG: WSManager уже запущен, игнорирую команду start().")

    async def _main_loop(self):
        self.logger.info("WSManager: _main_loop() запущен.")
        reconnect_delay = 5
        
        while self._is_running:
            try:
                self.logger.debug("DEBUG: Начинается новая итерация _main_loop.")
                
                if self._session is None or self._session.closed:
                    self.logger.debug("DEBUG: Сессия aiohttp закрыта или отсутствует, создаю новую.")
                    self._session = aiohttp.ClientSession()

                # Всегда запрашиваем новый токен при каждой попытке подключения
                self.logger.debug("DEBUG: Запрашиваю новый токен аутентификации для WebSocket.")
                self._websocket_auth_token = await request_auth_token(
                    logger_instance=self.logger,
                    session=self._session,
                    auth_token_rest_endpoint=self._auth_token_rest_endpoint,
                    api_key=self._api_key,
                    bot_name=self._bot_name
                )
                if self._websocket_auth_token is None:
                    self.logger.error(f"Не удалось получить токен аутентификации через REST. Повтор через {reconnect_delay}с.")
                    await asyncio.sleep(reconnect_delay)
                    self._websocket_auth_token = None # Убедимся, что токен сброшен
                    continue # Повторяем попытку получить токен
                
                ws_connect_url = (
                    self._ws_url
                    .replace('http://', 'ws://')
                    .replace('https://', 'wss://')
                )
                auth_ws_url = ws_connect_url
                
                self.logger.info(f"WSManager: Подключаемся к: {auth_ws_url}")
                self.logger.debug(f"DEBUG: URL для WebSocket подключения: {auth_ws_url}")

                async with self._session.ws_connect(auth_ws_url, timeout=10) as ws:
                    self._ws = ws
                    self.logger.info("WSManager: ✅ WebSocket подключен")
                    
                    auth_message = {
                        "command": "validate_token_rpc",
                        "token": self._websocket_auth_token,
                        "client_type": "DISCORD_BOT",
                        "bot_name": self._bot_name
                    }
                    await self._ws.send_str(json.dumps(auth_message))
                    self.logger.info("WSManager: Аутентификационные данные отправлены по WebSocket.")
                    self.logger.debug(f"DEBUG: Отправленные аутентификационные данные: {auth_message}")

                    self.logger.debug("DEBUG: Ожидаю сообщение подтверждения аутентификации от сервера.")
                    auth_confirm_msg = await asyncio.wait_for(ws.receive(), timeout=5)
                    self.logger.debug(f"DEBUG: Получено сырое сообщение подтверждения аутентификации. Тип: {auth_confirm_msg.type}, Данные: {auth_confirm_msg.data}")
                    
                    if auth_confirm_msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            confirm_data = json.loads(auth_confirm_msg.data)
                            self.logger.debug(f"DEBUG: Получен JSON подтверждения аутентификации: {confirm_data}")
                            ws_response_message = WebSocketMessage.model_validate(confirm_data)
                            self.logger.debug(f"DEBUG: Валидированное WebSocketMessage подтверждения: Тип={ws_response_message.type}, Статус={ws_response_message.payload.get('status') if ws_response_message.payload else 'Payload Missing'}")

                            rpc_payload = ws_response_message.payload
                            
                            if not rpc_payload:
                                await handle_auth_invalid_data(self.logger, confirm_data) 
                                self.logger.error("WSManager: Payload подтверждения аутентификации пуст или некорректен. Повтор запроса токена.")
                                self._websocket_auth_token = None # Инвалидируем токен
                                continue # Повторяем цикл для получения нового токена

                            response_status = rpc_payload.get("status")
                            if isinstance(response_status, str):
                                response_status_lower = response_status.lower()
                            else:
                                response_status_lower = None

                            self.logger.debug(f"DEBUG: Статус аутентификации из RPC payload: '{response_status_lower}' (original: {response_status})")

                            if ws_response_message.type == "AUTH_CONFIRM" and response_status_lower == "success":
                                client_id_from_server = rpc_payload.get("data", {}).get("client_id")
                                client_type_from_server = rpc_payload.get("data", {}).get("client_type")
                                
                                if client_id_from_server and client_type_from_server:
                                    await handle_auth_success(self.logger, client_id_from_server, client_type_from_server)
                                else:
                                    await handle_auth_invalid_data(self.logger, confirm_data)
                                    self.logger.error("WSManager: Данные client_id или client_type отсутствуют в успешном подтверждении аутентификации. Повтор запроса токена.")
                                    self._websocket_auth_token = None # Инвалидируем токен
                                    continue # Повторяем цикл для получения нового токена
                            else:
                                await handle_auth_error_response(self.logger, rpc_payload)
                                self.logger.error("WSManager: Аутентификация отклонена сервером. Повтор запроса токена.")
                                self._websocket_auth_token = None # Инвалидируем токен
                                continue # Повторяем цикл для получения нового токена

                        except json.JSONDecodeError as e: 
                            await handle_json_decode_error(self.logger, auth_confirm_msg.data)
                            self.logger.error(f"WSManager: Ошибка декодирования JSON в подтверждении аутентификации: {e}. Повтор запроса токена.")
                            self._websocket_auth_token = None # Инвалидируем токен
                            continue # Повторяем цикл для получения нового токена
                        except Exception as e:
                            self.logger.error(f"WSManager: Общая ошибка при обработке подтверждения аутентификации: {e}", exc_info=True)
                            self.logger.error("WSManager: Непредвиденная ошибка при обработке подтверждения аутентификации. Повтор запроса токена.")
                            self._websocket_auth_token = None # Инвалидируем токен
                            continue # Повторяем цикл для получения нового токена
                    else:
                        await handle_non_text_message(self.logger, auth_confirm_msg.type)
                        self.logger.error(f"WSManager: Получено нетекстовое сообщение подтверждения аутентификации (тип: {auth_confirm_msg.type}). Повтор запроса токена.")
                        self._websocket_auth_token = None # Инвалидируем токен
                        continue # Повторяем цикл для получения нового токена
                    
                    self.logger.info("WSManager: Начало прослушивания сообщений.")
                    self.logger.debug("DEBUG: Вход в цикл прослушивания WebSocket сообщений.")
                    
                    async for msg in ws:
                        self.logger.debug(f"DEBUG: Получено WebSocket сообщение. Тип: {msg.type}.")
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._inbound_dispatcher.dispatch_message(msg.data)
                        elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSE):
                            self.logger.warning(f"WSManager: Соединение закрыто или произошла ошибка (тип: {msg.type}). Разрыв соединения.")
                            break # Выход из внутреннего цикла, чтобы переподключиться
                        elif msg.type == aiohttp.WSMsgType.PING:
                            self.logger.debug("WSManager: Получен PING, отправляю PONG.")
                            await ws.pong()
                        elif msg.type == aiohttp.WSMsgType.PONG:
                            self.logger.debug("DEBUG: Получен PONG.")
                        else:
                            self.logger.warning(f"WSManager: Получено неизвестное или необрабатываемое сообщение типа: {msg.type}")
            
            except asyncio.CancelledError:
                self.logger.info("WSManager: Задача подключения отменена.")
                self.logger.debug("DEBUG: Задача _main_loop отменена.")
                self._websocket_auth_token = None # Инвалидируем токен при отмене
                break # Выход из основного цикла
            except aiohttp.client_exceptions.ClientConnectorError as e:
                await handle_client_connector_error(self.logger, e, auth_ws_url)
                self.logger.error(f"WSManager: Ошибка подключения клиента: {e}. Повтор запроса токена.")
                self._websocket_auth_token = None # Инвалидируем токен при ошибке подключения
            except asyncio.TimeoutError as e:
                await handle_timeout_error(self.logger, e)
                self.logger.error(f"WSManager: Таймаут при подключении или ожидании подтверждения: {e}. Повтор запроса токена.")
                self._websocket_auth_token = None # Инвалидируем токен при таймауте
            except Exception as e:
                self.logger.critical(f"WSManager: Критическая ошибка в _main_loop (не связанная с аутентификацией токена): {e}", exc_info=True)
                self.logger.error("WSManager: Непредвиденная критическая ошибка. Повтор запроса токена.")
                self._websocket_auth_token = None # Инвалидируем токен при любой критической ошибке
            finally:
                self.logger.debug("DEBUG: Блок finally _main_loop. Закрытие ресурсов.")
                if self._ws:
                    self.logger.debug("DEBUG: Закрытие WebSocket.")
                    await self._ws.close()
                    self._ws = None
                if self._session and not self._session.closed:
                    self.logger.debug("DEBUG: Закрытие aiohttp.ClientSession.")
                    await self._session.close()
                    self._session = None
                
                # Всегда инвалидируем токен и запрашиваем новый при следующем цикле,
                # если _is_running (т.е. бот не отключен явно).
                if self._is_running:
                    self.logger.info("WSManager: Соединение разорвано. Токен аутентификации будет запрошен заново при следующем подключении.")
                    self._websocket_auth_token = None # Всегда сбрасываем токен при разрыве/переподключении
                    self.logger.info(f"WSManager: Повторное подключение через {reconnect_delay} сек...")
                    self.logger.debug(f"DEBUG: Подготовка к переподключению через {reconnect_delay} секунд.")
                    await asyncio.sleep(reconnect_delay)
                else:
                    self.logger.info("WSManager: Менеджер отключен. Пропуск повторного подключения.")

    async def send_command(self, command_type: str, command_payload: Dict, domain: str, discord_context: Dict) -> Tuple[Dict, Dict]:
        self.logger.debug(f"Вызван send_command с command_type='{command_type}', domain='{domain}'.")
        if not self._ws or self._ws.closed:
            self.logger.error("Невозможно отправить команду: WebSocket соединение не установлено.")
            raise ConnectionError("WebSocket соединение не установлено.")

        command_id = str(uuid.uuid4())
        self.logger.debug(f"Сгенерирован command_id: {command_id}")

        # 1. Контекст для Redis
        request_context = discord_context.copy()
        request_context.update({
            "correlation_id": command_id,
            "command": command_type,
            "domain": domain
        })
        self.logger.debug(f"Создан request_context для Redis: {request_context}")
        
        # 2. "Обертка" команды
        command_wrapper_payload = WebSocketCommandFromClientPayload(
            command_id=command_id,
            type=command_type,
            domain=domain,
            payload=command_payload
        )
        self.logger.debug(f"Создана 'обертка' команды (WebSocketCommandFromClientPayload): {command_wrapper_payload.model_dump()}")
        
        # 3. Финальное сообщение
        message = WebSocketMessage(
            type="COMMAND",
            correlation_id=command_id,
            payload=command_wrapper_payload
        )
        self.logger.debug(f"Сформировано финальное сообщение (WebSocketMessage) для отправки: {message.model_dump(mode='json')}")
        
        # 4. Создание ожидания
        future = await self.pending_requests.create_request(command_id, request_context)
        self.logger.debug(f"Создан Future в PendingRequestsManager для command_id: {command_id}")
        
        try:
            # 5. Отправка
            await self._ws.send_str(message.model_dump_json())
            self.logger.info(f"Команда '{command_type}' (ID: {command_id}) успешно отправлена в домен '{domain}'.")
        except Exception as e:
            self.logger.error(f"Ошибка при отправке команды '{command_type}' (ID: {command_id}): {e}", exc_info=True)
            self.pending_requests.remove_request(command_id) 
            raise

        # 6. Ожидание ответа
        self.logger.debug(f"Ожидание ответа для команды '{command_type}' (ID: {command_id})...")
        response, retrieved_context = await future
        self.logger.debug(f"Получен ответ на команду '{command_type}' (ID: {command_id}).")
        return response, retrieved_context

    async def disconnect(self):
        self.logger.info("WSManager: Начало процесса отключения.")
        self.logger.debug("DEBUG: Установка _is_running в False.")
        self._is_running = False
        if self._listen_task:
            self.logger.debug("DEBUG: Попытка отменить задачу прослушивания.")
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                self.logger.debug("DEBUG: Задача прослушивания успешно отменена (ожидаемое исключение).")
                pass 
            except Exception as e:
                self.logger.error(f"DEBUG: Неожиданная ошибка при отмене задачи прослушивания: {e}", exc_info=True)
            self._listen_task = None
            self.logger.info("WSManager: Задача прослушивания отменена.")
        
        if self._ws:
            self.logger.debug("DEBUG: Закрытие активного WebSocket-соединения.")
            await self._ws.close()
            self._ws = None
            self.logger.info("WSManager: WebSocket соединение закрыто.")
        if self._session and not self._session.closed:
            self.logger.debug("DEBUG: Закрытие aiohttp.ClientSession.")
            await self._session.close()
            self._session = None
            self.logger.info("WSManager: aiohttp.ClientSession закрыта.")
        self.logger.debug("DEBUG: Процесс отключения завершен.")