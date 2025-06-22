# api_fast/gateway/gateway_config.py

# Список Redis Streams, которые должен прослушивать наш Command Gateway.
# Это позволяет гибко добавлять новые очереди для шлюза без изменения его кода.
GATEWAY_LISTEN_STREAMS = [
    "stream:bot_tasks",
    # В будущем, когда появятся другие сервисы, можно будет добавить еще:
    # "stream:system_alerts",
    # "stream:chat_events",
]

# Имя группы потребителей. Все экземпляры шлюза будут частью этой группы.
GATEWAY_CONSUMER_GROUP_NAME = "gateway_consumers"

# Имя нашего экземпляра. В будущем может генерироваться динамически.
GATEWAY_CONSUMER_NAME = "gateway_instance_1"