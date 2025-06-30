# transport/websocket_client/ws_manager.py

import aiohttp
import asyncio
import uuid
import json
import logging
import os
from typing import Any, Dict, Optional, Tuple

# Убедитесь, что все необходимые импорты присутствуют
from game_server.app_discord_bot.transport.websocket_client.event_handlers import WSEventHandlers
from game_server.app_discord_bot.transport.websocket_client.system_command_handlers import WSSystemCommandHandlers
from game_server.common_contracts.shared_models.api_contracts import WebSocketCommandFromClientPayload, WebSocketMessage, WebSocketResponsePayload, ResponseStatus
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.config.discord_settings import GATEWAY_AUTH_TOKEN, GATEWAY_URL, GAME_SERVER_API
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache


class WebSocketManager:
    def __init__(self, bot, pending_requests_manager: PendingRequestsManager, 
                 bot_name: str, 
                 bot_cache: Optional[BotCache] = None):
        logger.info("WSManager: Начинается инициализация __init__.")
        self._bot = bot
        
        self._ws_url = GATEWAY_URL
        self._api_key = GATEWAY_AUTH_TOKEN
        
        self._rest_api_base_url = GAME_SERVER_API
        self._auth_token_rest_endpoint = f"{self._rest_api_base_url}/auth/token"

        if self._ws_url is None:
            raise ValueError("GATEWAY_URL не установлен в настройках!")
        if self._api_key is None:
            raise ValueError("GATEWAY_AUTH_TOKEN не установлен в настройках!")
        if self._rest_api_base_url is None:
            raise ValueError("GAME_SERVER_API не установлен в настройках!")
        
        self.pending_requests = pending_requests_manager
        
        self.event_handler = WSEventHandlers(bot)
        self.system_command_handler = WSSystemCommandHandlers(bot)
        
        self._bot_cache = bot_cache
        self._bot_name = bot_name

        self._session: Optional[aiohttp.ClientSession] = None
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._is_running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._websocket_auth_token: Optional[str] = None
        logger.info("WSManager: Инициализация __init__ завершена.")

    def start(self):
        """Запускает цикл подключения и прослушивания в фоновом режиме."""
        logger.info("WSManager: Вызван метод start().")
        if not self._is_running:
            self._is_running = True
            try:
                self._listen_task = asyncio.create_task(
                    self._main_loop(), 
                    name=f"WSManager_{self._bot_name}"
                )
                logger.info("WSManager: Задача _main_loop создана и запущена.")
            except Exception as e:
                logger.critical(f"Ошибка при создании задачи: {e}", exc_info=True)
                self._is_running = False
        else:
            logger.warning("WSManager: Попытка запустить уже запущенный менеджер.")

    async def _request_auth_token(self) -> Optional[str]:
        """Запрашивает токен аутентификации через REST API Gateway."""
        logger.info(f"WSManager: Запрос токена аутентификации через REST API по URL: {self._auth_token_rest_endpoint}")
        payload = {
            "client_type": "DISCORD_BOT",
            "bot_name": self._bot_name,
            "bot_secret": self._api_key
        }
        
        try:
            if self._session is None or self._session.closed:
                self._session = aiohttp.ClientSession()
                
            async with self._session.post(self._auth_token_rest_endpoint, json=payload, timeout=10) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get("success") and response_data.get("data") and response_data["data"].get("token"):
                        token = response_data["data"]["token"]
                        logger.info(f"WSManager: ✅ Токен аутентификации успешно получен: ...{token[-6:]}")
                        return token
                    else:
                        error_msg = response_data.get("message", response_data.get("error", "Неизвестная ошибка"))
                        logger.error(f"WSManager: Сервер отклонил запрос токена: {response.status} - {error_msg}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"WSManager: Ошибка REST запроса токена: HTTP {response.status} - {error_text}")
                    return None
        except asyncio.TimeoutError:
            logger.error("WSManager: Таймаут при запросе токена через REST API.")
            return None
        except aiohttp.ClientError as e:
            logger.error(f"WSManager: Ошибка HTTP клиента при запросе токена: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.critical(f"WSManager: Непредвиденная ошибка при запросе токена: {e}", exc_info=True)
            return None

    async def _main_loop(self):
        """Основной цикл для поддержания WebSocket-соединения."""
        logger.info("WSManager: _main_loop() запущен.")
        reconnect_delay = 5
        
        if not self._ws_url or not self._api_key or not self._rest_api_base_url:
            logger.error("Отсутствуют необходимые параметры для подключения!")
            return
            
        while self._is_running:
            try:
                # Шаг 1 - Получаем токен аутентификации
                if self._websocket_auth_token is None:
                    self._websocket_auth_token = await self._request_auth_token()
                    if self._websocket_auth_token is None:
                        logger.error("WSManager: Не удалось получить токен аутентификации. Повтор через 5с.")
                        await asyncio.sleep(reconnect_delay)
                        continue # Начинаем цикл заново для повторной попытки

                logger.info(f"WSManager: Попытка подключения к WebSocket...")
                
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession()
                    logger.info("WSManager: aiohttp.ClientSession создана (в _main_loop).")
                
                ws_connect_url = self._ws_url.replace('http://', 'ws://').replace('https://', 'wss://')
                
                logger.info(f"WSManager: Подключаемся к: {ws_connect_url}")
                
                async with self._session.ws_connect(ws_connect_url, timeout=10) as ws:
                    self._ws = ws
                    logger.info(f"WSManager: ✅ WebSocket подключен")
                    
                    # Шаг 2 - Аутентификация WebSocket (отправляем полученный токен)
                    auth_message = {
                        "token": self._websocket_auth_token,
                        "client_type": "DISCORD_BOT",
                        "bot_name": self._bot_name
                    }
                    await self._ws.send_str(json.dumps(auth_message))
                    logger.info("WSManager: Аутентификационные данные отправлены по WebSocket.")
                    
                    # Шаг 3 - Ожидаем подтверждение аутентификации от Gateway
                    logger.info("WSManager: Ожидаем подтверждение аутентификации от Gateway...")
                    auth_confirm_received = False
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            confirm_msg_str = msg.data # Получаем данные из WSMsgType.TEXT
                            confirm_data = json.loads(confirm_msg_str)
                            confirm_message = WebSocketMessage.model_validate(confirm_data)

                            # ИЗМЕНЕНО: Доступ к status как к элементу словаря
                            if confirm_message.type == "AUTH_CONFIRM" and confirm_message.payload and \
                               confirm_message.payload['status'] == ResponseStatus.SUCCESS:
                                logger.info("WSManager: ✅ Аутентификация WebSocket успешно подтверждена Gateway!")
                                auth_confirm_received = True
                            else:
                                error_details = confirm_message.payload.get('message', "Unknown error") # Используем .get() для безопасности
                                logger.warning(f"WSManager: Gateway отказал в аутентификации WebSocket: {error_details}. Соединение будет закрыто.")
                                await ws.close(code=aiohttp.WSCloseCode.POLICY_VIOLATION) # УДАЛЕНО: reason
                        else:
                            logger.error(f"WSManager: Получено неожиданное сообщение типа {msg.type} после аутентификации. Соединение будет закрыто.")
                            await ws.close(code=aiohttp.WSCloseCode.PROTOCOL_ERROR) # УДАЛЕНО: reason

                    except asyncio.TimeoutError:
                        logger.error("WSManager: Таймаут при ожидании подтверждения аутентификации от Gateway. Соединение будет закрыто.")
                        await ws.close(code=aiohttp.WSCloseCode.POLICY_VIOLATION) # УДАЛЕНО: reason
                    except json.JSONDecodeError:
                        logger.error(f"WSManager: Gateway отправил не-JSON сообщение после аутентификации. Соединение будет закрыто.")
                        await ws.close(code=aiohttp.WSCloseCode.INVALID_MESSAGE_DATA) # УДАЛЕНО: reason
                    except Exception as e:
                        logger.error(f"WSManager: Ошибка при обработке подтверждения аутентификации: {e}. Соединение будет закрыто.", exc_info=True)
                        await ws.close(code=aiohttp.WSCloseCode.INTERNAL_ERROR) # УДАЛЕНО: reason

                    if not auth_confirm_received:
                        logger.warning("WSManager: Аутентификация не подтверждена. Повторное подключение.")
                        break # Выход из async for loop, чтобы перезапустить _main_loop

                    # Основной цикл обработки сообщений (только если аутентификация подтверждена)
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            logger.debug(f"WSManager: Получено текстовое сообщение: {msg.data}")
                            await self._handle_text_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WSManager: Ошибка WebSocket: {msg.data}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.warning("WSManager: Соединение закрыто сервером.")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            logger.info("WSManager: Получен запрос на закрытие соединения.")
                            await ws.close()
                            break
                            
            except asyncio.CancelledError:
                logger.info("WSManager: Задача подключения отменена.")
                break
            except Exception as e:
                logger.critical(f"WSManager: Непредвиденная ошибка в _main_loop: {e}", exc_info=True)
            finally:
                if self._session and not self._session.closed:
                    await self._session.close()
                    self._session = None
                
                if self._is_running:
                    logger.info(f"WSManager: Повторное подключение через {reconnect_delay} сек...")
                    await asyncio.sleep(reconnect_delay)
                else:
                    logger.info("WSManager: Менеджер остановлен, выход из _main_loop.")
                    break

    async def _handle_text_message(self, text_data: str):
        """Обрабатывает входящие текстовые сообщения WebSocket."""
        try:
            data = json.loads(text_data)
            message = WebSocketMessage.model_validate(data)
            
            if message.type == "RESPONSE":
                success, context_data = await self.pending_requests.resolve_request(message.payload['request_id'], message.payload)
                if success and context_data:
                    logger.debug(f"Получен ответ для пользователя Discord {context_data.get('discord_user_id')}")
            elif message.type == "EVENT":
                await self.event_handler.handle_event(message.payload)
            elif message.type == "SYSTEM_COMMAND":
                await self.system_command_handler.handle_command(message.payload)
            elif message.type == "AUTH_CONFIRM":
                logger.info(f"WSManager: Получено AUTH_CONFIRM: {text_data}")
                pass
            else:
                logger.warning(f"WSManager: Неизвестный тип WebSocket сообщения (JSON): {message.type}")
        except json.JSONDecodeError:
            logger.info(f"WSManager: Получено не-JSON текстовое сообщение (ожидается JSON): {text_data}")
        except Exception as e:
            logger.error(f"WSManager: Ошибка при обработке текстового сообщения (JSON или другое): {e}. Данные: {text_data}", exc_info=True)

    async def send_command(self, command_type: str, command_payload: dict, 
                           discord_context: Dict[str, Any]) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """
        Отправляет команду на сервер и асинхронно ожидает ответ.
        
        Args:
            command_type: Тип команды для Gateway.
            command_payload: Полезная нагрузка команды для Gateway.
            discord_context: Словарь с контекстом Discord (user_id, channel_id, message_id и т.д.).
        
        Returns:
            Кортеж (ответ_от_gateway, контекст_запроса_из_redis).
        """
        if not self._ws or self._ws.closed:
            raise ConnectionError("WebSocket соединение не установлено.")
        
        command_id = uuid.uuid4()
        
        request_context = {
            "discord_user_id": discord_context.get("user_id"),
            "discord_channel_id": discord_context.get("channel_id"),
            "discord_message_id": discord_context.get("message_id"),
            "command_type": command_type,
            "original_interaction_id": discord_context.get("interaction_id")
        }

        payload = WebSocketCommandFromClientPayload(
            command_id=command_id, type=command_type, payload=command_payload
        )
        message = WebSocketMessage(type="COMMAND", correlation_id=command_id, payload=payload)
        
        future = await self.pending_requests.create_request(command_id, request_context)
        
        await self._ws.send_str(message.model_dump_json())
        logger.info(f"Отправлена команда '{command_type}' с ID {command_id}")
        
        response, retrieved_context = await future
        
        return response, retrieved_context

    async def disconnect(self):
        """Отключает WebSocket соединение."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            logger.info("WSManager: WebSocket соединение закрыто.")
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("WSManager: aiohttp.ClientSession закрыта.")
        self._is_running = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None
            logger.info("WSManager: Задача прослушивания отменена.")

    def get_client_id_by_websocket(self, ws_connection: Any) -> Optional[str]:
        """Возвращает ID клиента, связанный с данным WebSocket-соединением."""
        if self._ws and self._ws == ws_connection:
            return self._bot_name
        return None

    def get_client_type(self) -> str:
        """Возвращает тип клиента (например, 'DISCORD_BOT')."""
        return "DISCORD_BOT"
