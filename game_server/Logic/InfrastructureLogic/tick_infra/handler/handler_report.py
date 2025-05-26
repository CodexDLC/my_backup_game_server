import asyncio
import os
import json
import sys
from game_server.database.models.models import FinishHandler
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger


from datetime import datetime

now = datetime.now()

async def finalize_handler_report(batch_id, task_type, completed, failed_tasks, status="success", error_message=None, redis_client=None, db_session=None):
    report_data = {
        "batch_id": batch_id,
        "task_type": task_type,
        "completed_tasks": completed,
        "failed_tasks": json.dumps(failed_tasks),
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "error_message": error_message,
        "processed_by_coordinator": False
    }

    if redis_client:
        await redis_client.hset("finish_handlers_tick", batch_id, json.dumps(report_data))
        await redis_client.expire("finish_handlers_tick", 3600)  # ⏳ Установить TTL на 1 час
        await redis_client.hdel("active_handlers", batch_id)

    if db_session:
        try:
            finish_record = FinishHandler(
                batch_id=batch_id,
                task_type=task_type,
                completed_tasks=completed,
                failed_tasks=json.dumps(failed_tasks),
                status=status,
                error_message=error_message,
                timestamp=datetime.now(),
                processed_by_coordinator=False
            )
            db_session.add(finish_record)
            await db_session.commit()
            logger.info(f"✅ Отчет batch_id={batch_id} успешно сохранен в базу данных.")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при сохранении отчета batch_id={batch_id}: {e}")
            sys.exit(1)  # ⛔ Полностью завершает выполнение скрипта



