# game_server/Logic/DomainLogic/handlers_template/worker_item_template/item_batch_utils/item_db_persistence.py

from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.ORM_equipment_templates import EquipmentTemplateRepository
from game_server.services.logging.logging_setup import logger

# Импорт асинхронного репозитория для предметов



async def persist_item_templates_to_db(
    db_session: AsyncSession,
    generated_templates: List[Dict[str, Any]],
    log_prefix: str
) -> bool:
    """
    Сохраняет список сгенерированных шаблонов предметов в базу данных.
    Использует EquipmentTemplateRepository для массовой вставки/обновления.
    """
    if not generated_templates:
        logger.warning(f"{log_prefix} Нет шаблонов предметов для сохранения в БД.")
        return True # Считаем, что операция успешна, если нечего сохранять

    item_repo = EquipmentTemplateRepository(db_session)
    
    try:
        # Вся операция сохранения внутри одной асинхронной транзакции
        async with db_session.begin(): 
            upserted_count = await item_repo.upsert_many(generated_templates)
        logger.info(f"{log_prefix} Успешно сохранено/обновлено {upserted_count} шаблонов в БД.")
        return True

    except Exception as db_e:
        logger.error(f"{log_prefix} Критическая ошибка при сохранении шаблонов в БД: {db_e}", exc_info=True)
        # Исключение будет проброшено выше для обработки Celery-таской
        return False