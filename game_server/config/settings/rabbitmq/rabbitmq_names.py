# game_server/config/settings/rabbitMQ/rabbitmq_names.py

class Exchanges:
    """
    Имена обменников (Exchanges).
    Это главные "сортировочные центры" для сообщений.
    """
    # Для команд, инициированных клиентами (через Gateway)
    COMMANDS = "commands.exchange"
    # Для событий и ответов, публикуемых микросервисами
    EVENTS = "events.exchange"


class Queues:
    """
    Константные имена очередей (Queues).
    Это "почтовые ящики" для конкретных микросервисов.
    """
    # --- RPC ОЧЕРЕДИ (для синхронных вызовов) ---
    AUTH_VALIDATE_TOKEN_RPC = "rpc.auth.validate_token"
    AUTH_ISSUE_BOT_TOKEN_RPC = "rpc.auth.issue_token"
    
    # --- ОЧЕРЕДИ ДЛЯ КОМАНД (потребляются микросервисами) ---
    AUTH_COMMANDS = "q.commands.auth"
    COORDINATOR_COMMANDS = "q.commands.coordinator"
    SYSTEM_COMMANDS = "q.commands.system"
    SYSTEM_CACHE_REQUESTS = "q.system.cache_requests"


    # --- ОЧЕРЕДЬ ДЛЯ ИСХОДЯЩИХ СООБЩЕНИЙ (потребляется Gateway) ---
    # ✅ ЕДИНАЯ ОЧЕРЕДЬ для ВСЕХ сообщений, идущих к клиентам через WebSocket.
    GATEWAY_OUTBOUND_WS_MESSAGES = "q.gateway.outbound_ws_messages"    
    GATEWAY_INBOUND_EVENTS = "q.gateway.inbound_events"

 
class RoutingKeys:
    """
    Префиксы для ключей маршрутизации.
    Описывают "адрес на конверте" сообщения.
    """
    # ✅ ЕДИНЫЙ ПРЕФИКС для всех команд от клиентов.
    # Полный ключ будет выглядеть как: "command.auth.login" или "command.inventory.get_items"
    COMMAND_PREFIX = "command"

    # ✅ ЕДИНЫЙ ПРЕФИКС для всех ответов на команды клиентов.
    # Полный ключ: "response.auth.login.success"
    RESPONSE_PREFIX = "response"

    # ✅ ЕДИНЫЙ ПРЕФИКС для внутренних событий между микросервисами (для хореографии).
    # Полный ключ: "event.player.created"
    EVENT_PREFIX = "event"

