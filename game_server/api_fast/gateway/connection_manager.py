# api_fast/gateway/connection_manager.py

from typing import List, Dict, Any
from fastapi import WebSocket

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

class ConnectionManager:
    """
    Управляет активными WebSocket-соединениями с Discord-ботом.
    Теперь поддерживает множество соединений (хотя для бота ожидается одно)
    и предоставляет статус.
    """
    def __init__(self):
        logger.info("✅ ConnectionManager инициализирован.")
        # ИЗМЕНЕНО: Теперь список для поддержки нескольких соединений (хотя бот один)
        self.active_connections: List[WebSocket] = []
        self.connection_count = 0  # Добавлен счетчик активных соединений
        
    async def connect(self, websocket: WebSocket):
        """
        Регистрирует новое подключение от бота.
        Соединение ДОЛЖНО БЫТЬ ПРИНЯТО (websocket.accept()) ДО вызова этой функции.
        """
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: УДАЛИТЬ accept() ---
        # await websocket.accept() # <--- ЭТУ СТРОКУ НУЖНО УДАЛИТЬ!
        # ----------------------------------------

        # Если вы хотите разрешать только одно соединение от бота:
        if self.active_connections:
            logger.warning("Попытка нового подключения при уже существующем активном. Старое будет закрыто.")
            old_ws = self.active_connections[0]
            if not old_ws.client_state.closed:
                await old_ws.close(code=1011, reason="New connection superseded old one.")
            self.active_connections.clear()
            self.connection_count = 0

        self.active_connections.append(websocket)
        self.connection_count += 1
        logger.info(f"🔌 Бот подключился к шлюзу. Активных соединений: {self.connection_count}")


    def disconnect(self, websocket: WebSocket):
        """Отмечает, что бот отключился."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.connection_count -= 1
            logger.info(f"🔌 Бот отключился от шлюза. Активных соединений: {self.connection_count}")
        else:
            logger.warning("Попытка отключить несуществующее WebSocket соединение.")


    async def send_command(self, command: Dict[str, Any]):
        """
        Отправляет команду в активное WebSocket-соединение.
        Теперь перебирает все активные соединения, хотя для бота ожидается одно.
        """
        if self.active_connections:
            # Для вашего случая с одним ботом, можно просто отправлять первому в списке:
            target_websocket = self.active_connections[0]
            try:
                await target_websocket.send_json(command)
                logger.debug(f"Команда {command.get('type')}:{command.get('command_id')} отправлена боту.")
            except Exception as e:
                logger.error(f"Ошибка отправки команды боту: {e}")
                # Если произошла ошибка отправки, возможно, соединение нужно пометить как неактивное
                self.disconnect(target_websocket) # Это вызовет повторное подключение бота
        else:
            logger.warning(f"Нет активного подключения бота для отправки команды {command.get('command_id')}.")

    @property
    def status(self) -> Dict[str, Any]:
        """Возвращает текущий статус соединений."""
        return {
            "active_connections": self.connection_count,
            "protocol": "websocket",
            "message": "WebSocket gateway for Discord bot"
        }