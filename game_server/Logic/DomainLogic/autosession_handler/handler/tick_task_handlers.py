# tick_task_handlers.py


import asyncio
from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger
from game_server.Logic.DomainLogic.autosession_handler.handler.handler_report import finalize_handler_report



class BaseTaskHandler:
    def __init__(self, task_type, task_package):
        self.task_type = task_type
        self.batch_id = task_package.get("batch_id")  # Добавлено получение batch_id
        self.items = task_package.get("items", [])
        self.redis_client = task_package.get("redis_client")
        self.db_session = task_package.get("db_session")
        self.completed = 0
        self.failed_tasks = []

    async def process(self):
        raise NotImplementedError("Метод `process()` должен быть реализован.")

    async def finalize(self):
        await finalize_handler_report(
            batch_id=self.batch_id,
            task_type=self.task_type,
            completed=self.completed,
            failed_tasks=self.failed_tasks,
            redis_client=self.redis_client,
            db_session=self.db_session
        )
            
# Обработчик Crafting

class CraftingHandler(BaseTaskHandler):
    async def process(self):
        logger.debug(f"🚀 Начат процесс обработки Crafting ({len(self.items)} персонажей)")
        for character_id in self.items:
            try:
                await self.redis_client.set(f"tick_processed_{character_id}", "done")
                logger.debug(f"✅ Crafting завершён: character_id={character_id}")
                self.completed += 1
            except Exception as e:
                logger.error(f"❌ Ошибка в Crafting для character_id={character_id}: {e}")
                self.failed_tasks.append({"character_id": character_id, "reason": str(e)})
                await asyncio.sleep(1)
        await self.finalize()
        logger.debug(f"🏁 Обработка Crafting завершена! Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}")
        return f"Обработка crafting завершена. Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}"

class GeneralHandler(BaseTaskHandler):
    async def process(self):
        logger.debug(f"🚀 Начат процесс обработки General ({len(self.items)} персонажей)")
        for character_id in self.items:
            try:
                await self.redis_client.set(f"tick_processed_{character_id}", "done")
                logger.debug(f"✅ General завершён: character_id={character_id}")
                self.completed += 1
            except Exception as e:
                logger.error(f"❌ Ошибка в General для character_id={character_id}: {e}")
                self.failed_tasks.append({"character_id": character_id, "reason": str(e)})
                await asyncio.sleep(1)
        await self.finalize()
        logger.debug(f"🏁 Обработка General завершена! Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}")
        return f"Обработка general завершена. Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}"

class ExplorationHandler(BaseTaskHandler):
    async def process(self):
        logger.debug(f"🚀 Начат процесс обработки Exploration ({len(self.items)} персонажей)")

        # Собираем пакет данных перед записью
        tick_processed_batch = {}

        for character_id in self.items:
            try:
                # ✅ Изменяем `tick_status` только для одной записи
                if character_id == "1":  # <-- Проверяем нужного персонажа
                    await self.redis_client.hset("tick_status", f"tick_status_1_1747922194", "D")

                # ✅ Добавляем в `tick_processed_batch`, чтобы записать все одним вызовом
                tick_processed_batch[f"E,{character_id}"] = "done"

                self.completed += 1
            except Exception as e:
                logger.error(f"❌ Ошибка в Exploration для character_id={character_id}: {e}")
                self.failed_tasks.append({"character_id": character_id, "reason": str(e)})
                await asyncio.sleep(1)

        # ✅ Одна запись в Redis, вместо множества отдельных вызовов
        for key, value in tick_processed_batch.items():
            await self.redis_client.hset("tick_processed", key, value)

        await self.redis_client.hset("batch_status", self.batch_id, "done")
        logger.debug(f"🏁 batch_id={self.batch_id} обработан! Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}")

        await self.finalize()
        logger.debug(f"🏁 Обработка Exploration завершена! Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}")
        return f"Обработка exploration завершена. Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}"


class TradeHandler(BaseTaskHandler):
    async def process(self):
        logger.debug(f"🚀 Начат процесс обработки Trade ({len(self.items)} персонажей)")
        for character_id in self.items:
            try:
                await self.redis_client.set(f"tick_processed_{character_id}", "done")
                logger.debug(f"✅ Trade завершён: character_id={character_id}")
                self.completed += 1
            except Exception as e:
                logger.error(f"❌ Ошибка в Trade для character_id={character_id}: {e}")
                self.failed_tasks.append({"character_id": character_id, "reason": str(e)})
                await asyncio.sleep(1)
        logger.debug("🧹 Запущен метод finalize()")      
        await self.finalize()
        logger.debug(f"🏁 Обработка Trade завершена! Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}")
        return f"Обработка trade завершена. Успешно: {self.completed}, Ошибок: {len(self.failed_tasks)}"


# Фабрика обработчиков по типу задачи
def create_task_handler(task_type, task_package):
    mapping = {
        "exploration": ExplorationHandler,
        "crafting": CraftingHandler,
        "trade": TradeHandler,
        "general": GeneralHandler,
    }
    handler_class = mapping.get(task_type)
    if not handler_class:
        raise ValueError(f"Не найден обработчик для типа задачи: {task_type}")
    return handler_class(task_type, task_package)

# Функции-обёртки, которые можно использовать для совместимости с ранее существующими вызовами:
async def handle_exploration_task(task_package):
    handler = create_task_handler("exploration", task_package)
    return await handler.process()

async def handle_crafting_task(task_package):
    handler = create_task_handler("crafting", task_package)
    return await handler.process()

async def handle_trade_task(task_package):
    handler = create_task_handler("trade", task_package)
    return await handler.process()

async def handle_general_task(task_package):
    handler = create_task_handler("general", task_package)
    return await handler.process()
