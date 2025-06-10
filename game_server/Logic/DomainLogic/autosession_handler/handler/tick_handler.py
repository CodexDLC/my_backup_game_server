
# game_server\Logic\InfrastructureLogic\tick_infra\handler\tick_handler.py

import asyncio
import sys
import json
from game_server.Logic.DomainLogic.autosession_handler.handler.tick_task_handlers import create_task_handler
from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger

from datetime import datetime

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session_orm
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient




class BatchHandler:
    def __init__(self, batch_id, task_type):
        self.batch_id = batch_id
        self.task_type = task_type
        self.redis_client = CentralRedisClient()
        self.db_session_factory = get_db_session_orm

    async def set_status(self, status):
        report_data = json.dumps({
            "batch_id": self.batch_id,
            "task_type": self.task_type,
            "handler_name": f"Handler_{self.batch_id}",
            "status": status,
            "timestamp": datetime.now().isoformat(timespec='milliseconds')
        })
        await self.redis_client.hset("active_handlers", self.batch_id, report_data)

    async def confirm_start(self):
        await self.set_status("started")

    async def confirm_failed(self):
        await self.set_status("failed")

    async def confirm_completed(self):
        await self.set_status("completed")

    async def run(self, max_retries=5):  # ✅ Перенесён внутрь класса
        retry_count = 0

        while retry_count < max_retries:
            try:
                logger.info(f"🚀 BatchHandler запущен для batch_id={self.batch_id}, task_type={self.task_type}")
                raw_data = await self.redis_client.hget("processed_batches", self.batch_id)
                items = json.loads(raw_data) if raw_data else []

                db_session = await self.db_session_factory()
                async with db_session:
                    task_package = {
                        "redis_client": self.redis_client,
                        "db_session": db_session,
                        "items": items,
                        "batch_id": self.batch_id
                    }

                    handler = create_task_handler(self.task_type, task_package)
                    result = await handler.process()

                    # Устанавливаем статус "done" перед выходом
                    await self.set_status("done")                    
                    
                    # Отправка результата в Redis вместо return
                    await self.redis_client.hset("batch_results", self.batch_id, json.dumps(result))
                    return  # Завершаем выполнение

            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Ошибка в run для batch_id={self.batch_id}, попытка {retry_count}/{max_retries}: {e}")
                await asyncio.sleep(1)

        logger.error(f"🛑 Достигнут предел попыток ({max_retries}) для batch_id={self.batch_id}, обработка остановлена.")
        await self.set_status("failed")


async def main():
    if len(sys.argv) < 3:
        print("Usage: python batch_handler.py <batch_id> <task_type>")
        return 1

    batch_id = sys.argv[1]
    task_type = sys.argv[2]

    handler = BatchHandler(batch_id, task_type)

    try:
        await handler.confirm_start()
        await handler.run()
        await handler.confirm_completed()
    except Exception as e:
        logger.error(f"Ошибка обработки batch_id={batch_id}: {e}")
        await handler.confirm_failed()
        return 1

if __name__ == "__main__":
    asyncio.run(main())
