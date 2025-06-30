# game_server/config/settings/rabbitMQ/rabbitmq_topology.py

from .rabbitmq_names import Exchanges as Ex, Queues as Q, RoutingKeys as RK

# 1. ОПРЕДЕЛЯЕМ ОБМЕННИКИ (EXCHANGES)
# Сортировочный центр для входящих команд
COMMANDS_EXCHANGE = {"name": Ex.COMMANDS, "type": "topic", "durable": True}
# Сортировочный центр для исходящих ответов и внутренних событий
EVENTS_EXCHANGE = {"name": Ex.EVENTS, "type": "topic", "durable": True}


# 2. ОПРЕДЕЛЯЕМ ОЧЕРЕДИ (QUEUES)
# RPC очередь
AUTH_ISSUE_BOT_TOKEN_RPC = {"name": Q.AUTH_ISSUE_BOT_TOKEN_RPC, "durable": True}
AUTH_VALIDATE_TOKEN_RPC_QUEUE = {"name": Q.AUTH_VALIDATE_TOKEN_RPC, "durable": True}


# Очереди для команд, которые слушают микросервисы
AUTH_COMMANDS_QUEUE = {"name": Q.AUTH_COMMANDS, "durable": True}
COORDINATOR_COMMANDS_QUEUE = {"name": Q.COORDINATOR_COMMANDS, "durable": True}
SYSTEM_SERVICES_COMMANDS_QUEUE = {"name": Q.SYSTEM_COMMANDS, "durable": True}

# Единая очередь для всех исходящих сообщений к Gateway
GATEWAY_OUTBOUND_WS_MESSAGES_QUEUE = {"name": Q.GATEWAY_OUTBOUND_WS_MESSAGES, "durable": True}


# 3. ОПРЕДЕЛЯЕМ СТРУКТУРУ ДЛЯ АВТОМАТИЧЕСКОЙ НАСТРОЙКИ
RABBITMQ_TOPOLOGY_SETUP = [
    # --- Объявляем обменники ---
    {"type": "exchange", "spec": COMMANDS_EXCHANGE},
    {"type": "exchange", "spec": EVENTS_EXCHANGE},

    # --- Объявляем очереди ---
    {"type": "queue", "spec": AUTH_ISSUE_BOT_TOKEN_RPC},
    {"type": "queue", "spec": AUTH_VALIDATE_TOKEN_RPC_QUEUE},
    {"type": "queue", "spec": AUTH_COMMANDS_QUEUE},
    {"type": "queue", "spec": COORDINATOR_COMMANDS_QUEUE},
    {"type": "queue", "spec": SYSTEM_SERVICES_COMMANDS_QUEUE},
    {"type": "queue", "spec": GATEWAY_OUTBOUND_WS_MESSAGES_QUEUE},
    
    # --- СВЯЗИ (BINDINGS) ---
    # ✅ НОВЫЙ ПОДХОД: Привязки для команд на основе их СМЫСЛА, а не источника.

    # Сервис Авторизации слушает все команды, касающиеся домена "auth"
    {
        "type": "binding",
        "source": Ex.COMMANDS,
        "destination": Q.AUTH_COMMANDS,
        "routing_key": f"{RK.COMMAND_PREFIX}.auth.#"  # command.auth.*
    },
    # Сервис Координации слушает все команды, касающиеся домена "coordinator"
    {
        "type": "binding",
        "source": Ex.COMMANDS,
        "destination": Q.COORDINATOR_COMMANDS,
        "routing_key": f"{RK.COMMAND_PREFIX}.coordinator.#"  # command.coordinator.*
    },
    # Системный сервис слушает все команды, касающиеся домена "system"
    {
        "type": "binding",
        "source": Ex.COMMANDS,
        "destination": Q.SYSTEM_COMMANDS,
        "routing_key": f"{RK.COMMAND_PREFIX}.system.#"
    },
    # Системный сервис также слушает все команды, касающиеся домена "shard"
    {
        "type": "binding",
        "source": Ex.COMMANDS,
        "destination": Q.SYSTEM_COMMANDS,
        "routing_key": f"{RK.COMMAND_PREFIX}.shard.#"  # command.shard.*
    },
    # НОВОЕ: Системный сервис также слушает все команды, касающиеся домена "discord"
    {
        "type": "binding",
        "source": Ex.COMMANDS,
        "destination": Q.SYSTEM_COMMANDS,
        "routing_key": f"{RK.COMMAND_PREFIX}.discord.#"  # command.discord.* (для sync_config_from_bot и других команд Discord)
    },

    # ✅ НОВЫЙ ПОДХОД: Привязки для ЕДИНОЙ исходящей очереди Gateway
    # Эта очередь слушает ВСЕ ответы и события, предназначенные для клиентов.
    {
        "type": "binding",
        "source": Ex.EVENTS,
        "destination": Q.GATEWAY_OUTBOUND_WS_MESSAGES,
        "routing_key": f"{RK.RESPONSE_PREFIX}.#"  # response.# (ловит все ответы)
    },
    {
        "type": "binding",
        "source": Ex.EVENTS,
        "destination": Q.GATEWAY_OUTBOUND_WS_MESSAGES,
        "routing_key": f"{RK.EVENT_PREFIX}.#"  # event.# (ловит все события для клиентов)
    },
]
