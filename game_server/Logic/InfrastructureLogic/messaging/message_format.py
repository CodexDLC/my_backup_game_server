# game_server/Logic/InfrastructureLogic/messaging/message_format.py

import uuid
from datetime import datetime, timezone
from typing import Dict, Any

def create_message(payload: Dict[str, Any], version: str = "1.0") -> Dict[str, Any]:
    """
    Создает стандартизированное сообщение с metadata и payload.

    Args:
        payload: Полезная нагрузка сообщения (команда и ее данные).
        version: Версия формата сообщения.

    Returns:
        Словарь, представляющий собой сообщение в стандартном формате.
    """
    return {
        "metadata": {
            "message_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": version
        },
        "payload": payload
    }