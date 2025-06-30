# game_server/Logic/InfrastructureLogic/messaging/i_message_bus.py
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncIterator, Optional # 🔥 ДОБАВЛЕНО: Optional для аргументов

class IMessageBus(ABC):
    """
    Интерфейс для шины сообщений.
    Отражает методы, фактически реализованные в RabbitMQMessageBus.
    """

    @abstractmethod
    async def connect(self):
        """Устанавливает соединение с шиной сообщений."""
        pass

    @abstractmethod
    async def publish(self, exchange_name: str, routing_key: str, message: Dict[str, Any]):
        """Публикует сообщение в указанный обменник."""
        pass

    # 🔥 ИЗМЕНЕНИЕ: УДАЛЯЕМ старый subscribe, так как он заменен на consume
    # @abstractmethod
    # async def subscribe(self, queue_name: str) -> AsyncIterator[Dict[str, Any]]:
    #     if False:
    #         yield

    # 🔥 НОВОЕ: Добавляем consume как абстрактный метод, так как RabbitMQMessageBus его реализует.
    @abstractmethod
    async def consume(self, queue_name: str, callback: callable):
        """Начинает потребление сообщений из очереди с использованием колбэка."""
        pass

    @abstractmethod
    async def close(self):
        """Закрывает соединение с шиной сообщений."""
        pass

    # 🔥 НОВОЕ: Добавляем методы для управления топологией как абстрактные,
    # так как RabbitMQMessageBus их реализует и они являются частью его API.
    @abstractmethod
    async def declare_queue(self, name: str, durable: bool = True, arguments: Optional[Dict[str, Any]] = None):
        """Объявляет очередь."""
        pass

    @abstractmethod
    async def declare_exchange(self, name: str, type: str = 'topic', durable: bool = True):
        """Объявляет обменник."""
        pass

    @abstractmethod
    async def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str):
        """Привязывает очередь к обменнику."""
        pass
