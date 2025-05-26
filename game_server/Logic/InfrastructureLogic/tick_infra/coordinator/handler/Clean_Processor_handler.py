
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
import json



async def extract_active_handlers(redis_client):
    """Извлекает `active_handlers`, парсит JSON и возвращает 3 списка: batch_id, handler_name, status."""
    active_handlers_raw = await redis_client.hgetall("active_handlers")

    if not active_handlers_raw:
        logger.info("✅ `active_handlers` пуст, возвращаем три пустых списка.")
        return [], [], []

    batch_ids = []
    handler_names = []
    statuses = []

    for batch_id, json_data in active_handlers_raw.items():
        try:
            fixed_json = json_data.replace("'", "\"")  # 🔥 Заменяем кавычки перед парсингом
            parsed_data = json.loads(fixed_json)  
            
            batch_ids.append(parsed_data.get("batch_id"))
            handler_names.append(parsed_data.get("handler_name"))
            statuses.append(parsed_data.get("status"))
        except json.JSONDecodeError:
            logger.warning(f"⚠️ Ошибка парсинга JSON для batch_id={batch_id}, игнорируем!")



    logger.debug(f"🔍 Извлечено {len(batch_ids)} обработчиков.")
    return batch_ids, handler_names, statuses




async def process_batch_report(redis_client):
    """Извлекает `batch_id` + `status` в файл, а `failed_tasks` собирает в список."""
    batch_reports = await redis_client.hgetall("finish_handlers_tick")

    if not batch_reports:
        logger.info("✅ `finish_handlers_tick` пуст, нечего сохранять.")
        return [], []

    failed_tasks_list = []
    batch_status_list = []

    for batch_id, report_json in batch_reports.items():
        try:
            report_data = json.loads(report_json)

            # ✅ Добавляем `batch_id` + `status` в список
            batch_status_list.append({
                "batch_id": report_data.get("batch_id"),
                "status": report_data.get("status")
            })

            # ✅ Собираем `failed_tasks` в отдельный список
            failed_tasks = report_data.get("failed_tasks")
            if failed_tasks and failed_tasks != "[]":  # Проверяем, есть ли ошибки
                failed_tasks_list.extend(json.loads(failed_tasks))

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON для batch_id={batch_id}: {e}")

    # ✅ Записываем `batch_status_list` в файл
    with open("batch_status_report.json", "w", encoding="utf-8") as file:
        json.dump(batch_status_list, file, ensure_ascii=False, indent=4)

    logger.info("🏁 `batch_status_report.json` создан, `failed_tasks` собраны!")
    
    return batch_status_list, failed_tasks_list


async def cleanup_successful_handlers(redis_client, batch_status_list, batch_ids):
    """Удаляет `batch_id` из `active_handlers`, если его статус в `batch_status_list` == `"success"`."""
    if not batch_status_list or not batch_ids:
        logger.info("✅ Списки `batch_status_list` и `batch_ids` пусты, очистка не требуется.")
        return
    
    logger.info("🔍 Запуск сравнения `batch_status_list` и `batch_ids`...")

    active_handlers = await redis_client.hgetall("active_handlers")
    
    if not active_handlers:
        logger.info("✅ `active_handlers` пуст, нечего удалять.")
        return

    for batch_entry in batch_status_list:
        batch_id = batch_entry.get("batch_id")
        status = batch_entry.get("status")

        if batch_id in batch_ids and status == "success":
            await redis_client.hdel("active_handlers", batch_id)
            logger.debug(f"🗑 Удалён `batch_id={batch_id}` из `active_handlers`")

    logger.info("🏁 Очистка `active_handlers` завершена!")



async def cleanup_available_workers(redis_client, batch_status_list, failed_tasks_list, active_handlers):
    """Удаляет `batch_id` из `available_workers_archive`, если его статус `success`, он неактивен или имеет ошибки."""

    available_workers = await redis_client.hgetall("available_workers_archive")

    if not available_workers:
        logger.info("✅ `available_workers_archive` пуст, нечего удалять.")
        return

    batch_ids_to_remove = set()

    for batch_id, worker_data in available_workers.items():
        try:
            # 🔎 Проверяем, если `worker_data` — строка, заменяем кавычки для корректного JSON
            if isinstance(worker_data, str):
                worker_data = worker_data.replace("'", '"')  # ✅ Исправляем кавычки
            
            worker_info = json.loads(worker_data)  # ✅ Парсим JSON

            # ✅ Проверяем условия удаления
            if any(entry["batch_id"] == batch_id and entry["status"] == "success" for entry in batch_status_list):
                batch_ids_to_remove.add(batch_id)

            if any(entry["batch_id"] == batch_id for entry in failed_tasks_list):
                batch_ids_to_remove.add(batch_id)

            if batch_id not in active_handlers:
                batch_ids_to_remove.add(batch_id)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON для batch_id={batch_id}: {e}")

    # ✅ Удаляем `batch_id` из `available_workers_archive`
    for batch_id in batch_ids_to_remove:
        await redis_client.hdel("available_workers_archive", batch_id)
        logger.debug(f"🗑 Удалён `batch_id={batch_id}` из `available_workers_archive`")

    logger.info("🏁 Очистка `available_workers_archive` завершена!")


async def cleanup_batch_results(redis_client, batch_status_list, failed_tasks_list, active_handlers):
    """Удаляет `batch_id` из `batch_results`, если его статус `success`, он неактивен или имеет ошибки."""

    batch_results = await redis_client.hgetall("batch_results")

    if not batch_results:
        logger.info("✅ `batch_results` пуст, нечего удалять.")
        return

    batch_ids_to_remove = set()

    for batch_id, result_data in batch_results.items():
        try:
            # ✅ Декодируем JSON-результат
            result_info = json.loads(result_data)

            # ✅ Проверяем `batch_status_list`: если `success`, удаляем
            if any(entry["batch_id"] == batch_id and entry["status"] == "success" for entry in batch_status_list):
                batch_ids_to_remove.add(batch_id)

            # ✅ Проверяем `failed_tasks_list`: если `batch_id` там есть, удаляем
            if any(entry["batch_id"] == batch_id for entry in failed_tasks_list):
                batch_ids_to_remove.add(batch_id)

            # ✅ Проверяем `active_handlers`: если `batch_id` отсутствует, удаляем
            if batch_id not in active_handlers:
                batch_ids_to_remove.add(batch_id)

        except json.JSONDecodeError as e:
            logger.error(f"❌ Ошибка парсинга JSON для batch_id={batch_id}: {e}")

    # ✅ Удаляем `batch_id` из `batch_results`
    for batch_id in batch_ids_to_remove:
        await redis_client.hdel("batch_results", batch_id)
        logger.debug(f"🗑 Удалён `batch_id={batch_id}` из `batch_results`")

    logger.info("🏁 Очистка `batch_results` завершена!")



async def cleanup_tick_processed(redis_client, batch_status_list):
    """Удаляет `tick_processed`, если его статус `done` совпадает с `success` в `batch_status_list`."""

    tick_processed = await redis_client.hgetall("tick_processed")

    if not tick_processed:
        logger.info("✅ `tick_processed` пуст, нечего удалять.")
        return

    batch_ids_to_remove = set()

    for tick_key, status in tick_processed.items():
        if status == "done":
            try:
                # ✅ Парсим JSON-часть ключа
                tick_data = json.loads(tick_key.split(",", 1)[1].replace("'", "\""))
                batch_id = tick_data.get("tick_id")  # ✅ Получаем `tick_id`
                
                # ✅ Проверяем, есть ли `batch_id` в `batch_status_list`
                if any(entry["batch_id"] == batch_id and entry["status"] == "success" for entry in batch_status_list):
                    batch_ids_to_remove.add(tick_key)

            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON в tick_key: {tick_key}, {e}")

    # ✅ Удаляем `tick_processed` для завершённых задач
    for tick_key in batch_ids_to_remove:
        await redis_client.hdel("tick_processed", tick_key)
        logger.debug(f"🗑 Удалён `tick_processed` → {tick_key}")

    logger.info("🏁 Очистка `tick_processed` завершена!")

async def cleanup_processed_batches(redis_client, batch_status_list):
    """Удаляет `batch_id` из `processed_batches`, если его статус `success`."""

    processed_batches = await redis_client.hgetall("processed_batches")

    if not processed_batches:
        logger.info("✅ `processed_batches` пуст, нечего удалять.")
        return

    batch_ids_to_remove = {entry["batch_id"] for entry in batch_status_list if entry["status"] == "success"}

    for batch_id in batch_ids_to_remove:
        await redis_client.hdel("processed_batches", batch_id)
        logger.debug(f"🗑 Удалён `batch_id={batch_id}` из `processed_batches`")

    logger.info(f"🏁 Очистка `processed_batches` завершена! Удалено {len(batch_ids_to_remove)} записей.")


async def cleanup_batch_status(redis_client, batch_status_list):
    """Удаляет `batch_id` из `batch_status`, если его статус `success`."""
    
    if not batch_status_list:
        logger.info("✅ `batch_status_list` пуст, очистка не требуется.")
        return

    batch_status = await redis_client.hgetall("batch_status")

    if not batch_status:
        logger.info("✅ `batch_status` пуст, нечего удалять.")
        return

    batch_ids_to_remove = {entry["batch_id"] for entry in batch_status_list if entry["status"] == "success"}

    # ✅ Удаляем `batch_id` из `batch_status`
    for batch_id in batch_ids_to_remove:
        await redis_client.hdel("batch_status", batch_id)
        logger.debug(f"🗑 Удалён `batch_id={batch_id}` из `batch_status`")

    logger.info(f"🏁 Очистка `batch_status` завершена! Удалено {len(batch_ids_to_remove)} записей.")


async def cleanup_tick_status(redis_client):
    """Удаляет записи `tick_status`, если они имеют статус `done`."""
    logger.info("🗑 Запускаем очистку `tick_status`...")

    tick_statuses = await redis_client.hgetall("tick_status")
    if not tick_statuses:
        logger.info("✅ `tick_status` уже пуст, очистка не требуется.")
        return

    for tick_key, status in tick_statuses.items():
        if status == "done":  # 📌 Удаляем только завершённые
            await redis_client.hdel("tick_status", tick_key)
            logger.debug(f"🗑 Удалено `tick_status`: {tick_key}")
