# game_server/Logic/DomainLogic/arq_tasks/location_tasks.py

from datetime import datetime
import logging
import json
from typing import Dict, Any, Optional
import uuid

from game_server.contracts.shared_models.websocket_base_models import WebSocketEventPayload, WebSocketMessage

# Импортируем интерфейсы и зависимости, которые будут получены из контекста
from ...InfrastructureLogic.messaging.i_message_bus import IMessageBus
from ...InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository
from ...InfrastructureLogic.app_cache.interfaces.interfaces_dinamic_location_manager import IDynamicLocationManager
from ....config.settings.rabbitmq.rabbitmq_names import Exchanges, RoutingKeys


def _prepare_full_state_for_cache(location_state: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """
    ВНУТРЕННИЙ ХЕЛПЕР:
    Готовит данные из документа MongoDB для записи в кэш Redis.
    Сериализует поля-массивы в JSON-строки.
    """
    if not location_state:
        return {}

    cache_data = {}
    fields_to_serialize = ["players", "npcs", "items_on_ground", "resource_nodes", "location_effects"]

    for field in fields_to_serialize:
        data_list = location_state.get(field, [])
        cache_data[field] = json.dumps(data_list)
        
    # --- ИСПРАВЛЕННАЯ ЛОГИКА ---
    last_update_value = location_state.get("last_update")
    # ✅ ИЗМЕНЕНИЕ: Теперь мы можем использовать просто 'datetime'
    if isinstance(last_update_value, datetime):
        # Если это объект datetime, просто преобразуем его в строку
        cache_data["last_update"] = last_update_value.isoformat()
    elif isinstance(last_update_value, dict):
        # Если это словарь (как было раньше), достаем значение из '$date'
        cache_data["last_update"] = last_update_value.get("$date", "")

    return cache_data

async def aggregate_location_state(ctx: Dict[str, Any], location_id: str):
    """
    ARQ задача для обновления кэша (полное состояние) и отправки события.
    """
    # --- Получаем зависимости из ctx ---
    logger: logging.Logger = ctx["logger"]
    location_state_repo: ILocationStateRepository = ctx["location_state_repo"]
    dynamic_location_manager: IDynamicLocationManager = ctx["dynamic_location_manager"]
    message_bus: IMessageBus = ctx["message_bus"]
    
    log_prefix = f"ARQ_TASK (aggregate_location_state, loc_id: {location_id}):"
    logger.info(f"{log_prefix} Начало обработки.")

    try:
        # 1. Прочитать полный документ локации из MongoDB
        location_doc = await location_state_repo.get_location_by_id(location_id)
        if not location_doc:
            logger.warning(f"{log_prefix} Локация не найдена в MongoDB. Задача прервана.")
            return

        # 2. Подготовить ПОЛНЫЕ данные для кэша с помощью внутреннего хелпера
        cache_data_mapping = _prepare_full_state_for_cache(location_doc)
        
        # 3. Обновить ПОЛНЫЕ данные в центральном кэше Redis через менеджер
        await dynamic_location_manager.update_location_summary(location_id, cache_data_mapping)
        
        # --- Step 4: CORRECT message creation ---

        # 4.1. The innermost payload is just the simple data.
        event_data_payload = {"location_id": location_id}

        # 4.2. This is wrapped in the WebSocketEventPayload.
        # The 'type' here is the specific event name.
        event_payload = WebSocketEventPayload(
            type="event.location.updated",
            payload=event_data_payload
        )

        # 4.3. This is wrapped in the main WebSocketMessage "envelope".
        # The 'type' here is always "EVENT".
        websocket_message = WebSocketMessage(
            type="EVENT",
            correlation_id=uuid.uuid4(),
            payload=event_payload
        )
        
        # 4.4. Publish the correctly structured message.
        event_routing_key = "event.location.updated"
        await message_bus.publish(
            exchange_name=Exchanges.EVENTS,
            routing_key=event_routing_key,
            message=websocket_message.model_dump(mode='json')
        )
        logger.info(f"[ARQ Task] Event '{event_routing_key}' for location {location_id} sent.")

    except Exception as e:
        logger.critical(f"[ARQ Task] Critical error processing location {location_id}: {e}", exc_info=True)
        raise

class WorkerSettings:
    functions = [aggregate_location_state]