
# game_server\Logic\InfrastructureLogic\tick_infra\collector\handler\tick_collector_handler.py


import json
from datetime import timedelta
import time
from sqlalchemy import func
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.task_utils import get_tick_status, set_tick_status
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
from game_server.Logic.DataAccessLogic.db_in import AsyncDatabase

# Импорт функции для фоновой обработки очереди из очередного модуля:


async def get_ready_characters(db: AsyncDatabase):
    """Выбирает готовых персонажей по `next_tick_at` и конвертирует поле `active_category` в `task_type`."""
    logger.debug("🔎 Запуск фильтрации персонажей через пул соединений...")

    query = "SELECT * FROM auto_sessions WHERE next_tick_at <= NOW()"
    try:
        logger.debug(f"🔍 Выполняем запрос: {query}")
        rows = await db.get_data(query)
        logger.debug(f"🧐 Полученные данные: {rows}")

        characters = []
        for row in rows:
            character = dict(row)
            if 'active_category' in character:
                character['task_type'] = character.pop('active_category')
            characters.append(character)

        logger.info(f"✅ Обработано {len(characters)} персонажей.")  # 🔹 Итоговый лог в `INFO`
        return characters
    except Exception as e:
        logger.error(f"❌ Ошибка при фильтрации данных: {e}", exc_info=True)
        return []


async def send_to_redis(active_sessions, redis_client, tick_id):
    """Записывает персонажей с привязкой к конкретному тику в компактном формате."""
    try:
        logger.debug(f"📤 Готовимся записать {len(active_sessions)} персонажей в Redis...")

        for session in active_sessions:
            short_code = f"{session['task_type'][0].upper()}:{session['character_id']}:{tick_id}"  # E, C, T
            await redis_client.rpush("tick_processing_queue", short_code)

            # ✅ Используем `set_tick_status()`
            await set_tick_status(redis_client, session['character_id'], tick_id, "I")

            logger.debug(f"🟢 Записан персонаж {session['character_id']} → Тик: {tick_id}, Тип: {session['task_type']}.")

        logger.info(f"✅ Запись завершена! {len(active_sessions)} персонажей успешно сохранены в Redis.")

    except Exception as e:
        logger.error(f"❌ Ошибка записи в Redis: {e}", exc_info=True)

       

async def update_tick_info(character_id: int, db: AsyncDatabase):
    """Обновляет `last_tick_at` и `next_tick_at` через переданное подключение `db`."""
    logger.debug(f"🔄 Начинаем обновление данных персонажа {character_id}...")  # 🔹 `DEBUG` перед обработкой

    query_select = "SELECT last_tick_at, next_tick_at FROM auto_sessions WHERE character_id = $1"
    query_update = "UPDATE auto_sessions SET last_tick_at = $1, next_tick_at = $2 WHERE character_id = $3"

    updated_count = 0  # ✅ Инициализируем счетчик

    try:
        char = await db.get_data(query_select, character_id)  # ✅ Читаем данные через `db`

        if char:
            char = char[0]  # ✅ `get_data()` возвращает список, берём первый элемент
            logger.debug(f"🔍 Данные персонажа {character_id}: last_tick_at={char['last_tick_at']}, next_tick_at={char['next_tick_at']}")

            # 🔄 Обновляем параметры тика
            new_last_tick = char['next_tick_at']
            new_next_tick = new_last_tick + timedelta(minutes=1)

            # ✅ Обновляем запись в БД
            await db.save_data(query_update, new_last_tick, new_next_tick, character_id)

            updated_count += 1  # ✅ Увеличиваем счетчик при успешном обновлении
            
            logger.debug(f"✅ Обновлено last_tick_at={new_last_tick}, next_tick_at={new_next_tick} для персонажа {character_id}.")
        else:
            logger.warning(f"⚠ Персонаж {character_id} не найден в базе.")  # 🔹 `WARNING`, если персонаж отсутствует

    except Exception as e:
        logger.error(f"❌ Ошибка обновления персонажа {character_id}: {e}", exc_info=True)  # 🔹 `ERROR` в случае ошибки
    
    # ✅ Итоговый `INFO`-лог в конце
    logger.info(f"✅ Завершено обновление тиков. Успешно обновлено {updated_count} персонажей.")


async def fetch_and_process_tasks(redis_client):
    """Получает задачи из `tick_processing_queue`, проверяет статус и сортирует."""
    logger.debug("🔄 Запуск обработки задач из `tick_processing_queue`...")  # 🔹 `DEBUG` перед началом

    raw_tasks = await redis_client.lrange("tick_processing_queue", 0, -1)

    if not raw_tasks:
        logger.info("✅ Очередь пуста, нет задач для обработки.")  # 🔹 `INFO` финальный результат
        return []

    parsed_tasks = []
    for task in raw_tasks:
        task = task.decode("utf-8") if isinstance(task, bytes) else task
        parts = task.split(":")
        
        if len(parts) != 3:
            logger.warning(f"⚠ Некорректный формат задачи: {task}")  # 🔹 `WARNING`, если формат неверный
            continue

        task_type, character_id, tick_id = parts
        flag = await get_tick_status(redis_client, character_id, tick_id)

        if flag != "I":
            logger.debug(f"🔕 Пропущена задача `{task}` (статус: {flag})")  # 🔹 `DEBUG`, если статус не `I`
            continue

        parsed_tasks.append({
            "task_type": task_type,
            "character_id": character_id,
            "tick_id": tick_id
        })
    
    logger.info(f"✅ Обработано {len(parsed_tasks)} задач из `tick_processing_queue`.")  # 🔹 `INFO` итог
    return parsed_tasks


async def categorize_tasks(parsed_tasks, redis_client):
    """Группирует задачи по `task_type`, создаёт `batch_id`, сохраняет в Redis."""
    logger.debug("🔄 Запуск группировки задач по `task_type`...")

    task_groups = {}
    server_start_time = int(await redis_client.get("server_start_time") or time.time())
    batch_counter = int(await redis_client.get("batch_counter") or 1)

    for task in parsed_tasks:
        task_type = task["task_type"]
        batch_id = f"{task_type}_{server_start_time}_{batch_counter}"

        if len(task_groups.get(batch_id, [])) >= 100:
            batch_counter += 1
            batch_id = f"{task_type}_{server_start_time}_{batch_counter}"

        task_groups.setdefault(batch_id, []).append(task)
        logger.debug(f"📦 Добавлена задача `{task}` в batch `{batch_id}`.")

    for batch_id, tasks in task_groups.items():
        await redis_client.hset("processed_batches", batch_id, json.dumps(tasks))
        await redis_client.hset("batch_status", batch_id, "initiation")
        logger.debug(f"🗃️ Сохранен batch `{batch_id}` с {len(tasks)} задачами.")

    await redis_client.set("batch_counter", batch_counter)
    logger.info(f"✅ Группировка завершена! Создано {len(task_groups)} batch.")
    
    return task_groups


async def cleanup_tick_processing_queue(redis_client):
    """Проверяет, содержат ли все `processed_batches` задачи из `tick_processing_queue`. Если да — обновляет их статус на `done` и очищает `tick_processing_queue`."""
    
    logger.debug("🔄 Запуск сравнения `tick_processing_queue` и `processed_batches`...")  

    raw_tasks = await redis_client.lrange("tick_processing_queue", 0, -1)
    if not raw_tasks:
        logger.info("✅ `tick_processing_queue` уже пуст, очистка не требуется.")  
        return

    task_set = set(raw_tasks)
    logger.debug(f"📦 Загружено {len(task_set)} задач из `tick_processing_queue`.")

    processed_batches_raw = await redis_client.hgetall("processed_batches")
    
    if not processed_batches_raw:
        logger.warning("⚠ `processed_batches` пуст, сравнение невозможно!")  
        return
    
    batch_task_set = set()
    for batch_id, tasks_json in processed_batches_raw.items():
        tasks = json.loads(tasks_json)
        for task in tasks:
            batch_task_set.add(f"{task['task_type']}:{task['character_id']}:{task['tick_id']}")  

    logger.debug(f"🗂️ Загружено {len(batch_task_set)} задач из `processed_batches` для сравнения.")

    if task_set.issubset(batch_task_set):
        logger.info("✅ Все задачи перенесены в `processed_batches`, обновляем статус `tick_status` → `done`...")
        
        for task in task_set:
            task_parts = task.split(":")
            if len(task_parts) >= 3:
                tick_key = f"tick_status_{task_parts[1]}_{task_parts[2]}"  
                await redis_client.hset("tick_status", tick_key, "done")
                logger.debug(f"🟢 Обновлён статус `{tick_key}` → `done`")

        await redis_client.delete("tick_processing_queue")  
        logger.info("🏁 Очистка `tick_processing_queue` завершена!")
    else:
        remaining_tasks = task_set - batch_task_set
        logger.debug(f"🔍 Осталось {len(remaining_tasks)} задач, которые не найдены в `processed_batches`.")
        logger.info("🔄 Некоторые задачи отсутствуют в `processed_batches`, очистка `tick_processing_queue` не производится.")

