
import asyncio
import sys
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger  # Импортируем логгер



WORKER_DISTRIBUTION = {
    "exploration": 0.5,  # 50%
    "crafting": 0.2,  # 20%
    "trade": 0.2,  # 20%
    "other": 0.1,  # 10%
}

queue_names = [
"tick_exploration",
"tick_crafting", 
"tick_trade", 
"tick_general"
]


MAX_WORKERS = 10  # 🔹 Легко меняемое количество воркеров


async def get_initiation_batches(redis_client):
    """
    Получает список batch_id со статусом 'initiation' из Redis.
    Возвращает список или пустой список, если нет подходящих записей.
    Логирует ключевые этапы работы и возможные проблемы.
    """
    try:
        # Логируем начало операции
        logger.debug("Начало получения batch_id со статусом 'initiation'")
        
        # Получаем все записи статусов
        batch_status_all = await redis_client.hgetall("batch_status")
        logger.debug(f"Получено записей из Redis: {len(batch_status_all)}")
        
        if not batch_status_all:
            logger.info("В Redis отсутствуют данные в hash 'batch_status'")
            return []
        
        # Фильтруем только initiation статусы
        initiation_batches = [
            batch_id 
            for batch_id, status in batch_status_all.items() 
            if status == "initiation"
        ]
        
        # Логируем результат
        if initiation_batches:
            logger.info(f"Найдено batch_id в статусе 'initiation': {len(initiation_batches)}")
        else:
            logger.info("Записи со статусом 'initiation' отсутствуют")
        
        return initiation_batches
        
    except Exception as e:
        logger.error(f"Ошибка при получении batch_id: {str(e)}", exc_info=True)
        raise  # Пробрасываем исключение дальше для обработки вызывающей стороной

def calculate_free_workers():
    free_workers = {
        task_type: max(1, int(MAX_WORKERS * ratio))
        for task_type, ratio in WORKER_DISTRIBUTION.items()
    }
    return free_workers


async def get_available_batches(initiation_batches, free_workers, redis_client):
    """Распределяет batch_id по воркерам и сохраняет результат в Redis."""
    task_type_map = {"E": "exploration", "C": "crafting", "T": "trade", "O": "other"}
    max_to_process = 10
    initiation_batches_process = initiation_batches[:max_to_process]
    available_workers = []
    free_workers_copy = free_workers.copy()

    # 1. Распределение задач по воркерам (прежняя логика)
    leftovers = []
    for batch_id in initiation_batches_process:
        prefix = batch_id.split("_")[0]
        task_type = task_type_map.get(prefix)
        if task_type and free_workers_copy.get(task_type, 0) > 0:
            available_workers.append({
                "batch_id": batch_id,
                "task_type": task_type,
                "original_task_type": task_type
            })
            free_workers_copy[task_type] -= 1
        else:
            leftovers.append(batch_id)

    # 2. Перераспределение остатков (прежняя логика)
    if leftovers:
        total_free = sum(free_workers_copy.values())
        if total_free > 0:
            for batch_id in leftovers:
                prefix = batch_id.split("_")[0]
                task_type = task_type_map.get(prefix)
                if not task_type:
                    continue
                for wt, count in free_workers_copy.items():
                    if count > 0:
                        available_workers.append({
                            "batch_id": batch_id,
                            "task_type": task_type,
                            "original_task_type": wt
                        })
                        free_workers_copy[wt] -= 1
                        break

    # 3. 🔥 Сохранение в Redis (исправлено!)
    if available_workers:  # сохраняем только если есть данные
        import uuid
        archive_id = str(uuid.uuid4())  # уникальный ID для архива
        await redis_client.hset(
            "available_workers_archive",
            archive_id,
            str(available_workers)  # или json.dumps(available_workers)
        )
        logger.info(f"🗄 Список available_workers сохранён в архив под ключом: {archive_id}")
    else:
        logger.info("⚠️ Нет данных для архивации (available_workers пуст)")

    return available_workers





async def run_worker(batch_id, task_type):
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, 'game_server/Logic/InfrastructureLogic/tick_infra/handler/tick_handler.py',
            batch_id, task_type,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            logger.warning(f"⚠️ Таймаут у воркера batch_id={batch_id}")
            return

        if process.returncode != 0:
            logger.error(f"❌ Воркер batch_id={batch_id} завершился с ошибкой: {stderr.decode()}")
        else:
            logger.info(f"✅ Воркер batch_id={batch_id} завершил работу.\nstdout: {stdout.decode()}")

    except Exception as e:
        logger.error(f"❌ Ошибка запуска воркера batch_id={batch_id}: {e}", exc_info=True)



async def process_available_batches(redis_client, available_workers):
    if not available_workers:
        logger.info("✅ Нет доступных задач, завершаем `process_available_batches`.")
        return []

    completed_batches = []
    i = 0
    while i < len(available_workers):
        try:
            batch_info = available_workers[i]
            batch_id = batch_info["batch_id"]
            task_type = batch_info["task_type"]

            logger.debug(f"🔍 [DEBUG] Проверка `batch_status` для `batch_id={batch_id}`...")
            current_status = await redis_client.hget("batch_status", batch_id)

            if current_status == "done":
                logger.debug(f"✅ [DEBUG] batch_id={batch_id} уже завершён, удаляем из списка.")
                available_workers.pop(i)
                completed_batches.append(batch_id)
                continue

            logger.info(f"🚀 Запускаем обработку `batch_id={batch_id}` в субпроцессе...")

            process = await asyncio.create_subprocess_exec(
                'python', 'game_server/Logic/InfrastructureLogic/tick_infra/handler/tick_handler.py', batch_id, task_type,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Время ожидания отчёта от batch_id={batch_id} истекло, оставляем задачу в списке.")
                i += 1
                continue

            logger.info(f"🛠 Воркер `{batch_id}` завершил работу.\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}")
            completed_batches.append(batch_id)
            available_workers.pop(i)

        except Exception as e:
            logger.error(f"❌ Ошибка в `process_available_batches`: {e}", exc_info=True)
            i += 1
            continue

    return completed_batches



   
async def process_tasks(redis_client):
    initiation_batches = await get_initiation_batches(redis_client)

    while initiation_batches:
        free_workers = calculate_free_workers()

        available_workers = await get_available_batches(initiation_batches, free_workers, redis_client)
        if not available_workers:
            break

        completed_batches = await process_available_batches(redis_client, available_workers)

        for batch_id in completed_batches:
            await redis_client.hset("batch_status", batch_id, "done")

        initiation_batches = [b for b in initiation_batches if b not in completed_batches]

        await asyncio.sleep(2)



