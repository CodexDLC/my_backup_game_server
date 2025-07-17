# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_1lvl/equipment_template_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import func # Добавлен func для count

# Импорт модели EquipmentTemplate
from game_server.database.models.models import EquipmentTemplate

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class EquipmentTemplateRepositoryImpl(IEquipmentTemplateRepository):
    """
    Репозиторий для управления объектами EquipmentTemplate в базе данных (асинхронный).
    Реализует интерфейс IEquipmentTemplateRepository.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.debug(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает новый шаблон предмета снаряжения в рамках переданной сессии.
        """
        new_template = EquipmentTemplate(**data)
        self._session.add(new_template)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Шаблон предмета снаряжения '{new_template.item_code}' добавлен в сессию.")
        return new_template

    async def get_by_id(self, id: int) -> Optional[EquipmentTemplate]:
        """
        Получает шаблон по его числовому идентификатору (id) в рамках переданной сессии.
        """
        stmt = fselect(EquipmentTemplate).where(EquipmentTemplate.id == id) # Предполагается наличие поля 'id'
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_item_code(self, item_code: str) -> Optional[EquipmentTemplate]:
        """
        Получает шаблон по его item_code в рамках переданной сессии.
        """
        stmt = fselect(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_item_codes(self) -> List[str]:
        """
        Получает все item_code существующих шаблонов предметов снаряжения в рамках переданной сессии.
        """
        stmt = fselect(EquipmentTemplate.item_code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all(self) -> List[EquipmentTemplate]:
        """
        Получает все шаблоны предметов снаряжения из базы данных в рамках переданной сессии.
        Соответствует методу get_all интерфейса.
        """
        stmt = fselect(EquipmentTemplate)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_templates(self) -> List[EquipmentTemplate]:
        """
        Получает все шаблоны предметов снаряжения в рамках переданной сессии.
        (Этот метод не был в интерфейсе, но может быть полезен. Оставляем.)
        """
        return await self.get_all() # Переиспользуем get_all, чтобы избежать дублирования логики

    async def update(self, item_code: str, updates: Dict[str, Any]) -> Optional[EquipmentTemplate]:
        """
        Обновляет существующий шаблон по его item_code в рамках переданной сессии.
        """
        stmt = update(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code).values(**updates).returning(EquipmentTemplate)
        result = await self._session.execute(stmt)
        updated_template = result.scalars().first()
        if updated_template:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шаблон (item_code: {item_code}) обновлен в сессии.")
        else:
            logger.warning(f"Шаблон с item_code {item_code} не найден для обновления.")
        return updated_template

    async def delete(self, id: int) -> bool:
        """
        Удаляет шаблон по его числовому идентификатору (id) в рамках переданной сессии.
        """
        stmt = delete(EquipmentTemplate).where(EquipmentTemplate.id == id) # Предполагается наличие поля 'id'
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шаблон (ID: {id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Шаблон с ID {id} не найден для удаления.")
            return False

    async def delete_by_item_code(self, item_code: str) -> bool:
        """
        Удаляет шаблон по его item_code в рамках переданной сессии.
        """
        stmt = delete(EquipmentTemplate).where(EquipmentTemplate.item_code == item_code)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шаблон (item_code: {item_code}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Шаблон с item_code {item_code} не найден для удаления.")
            return False

    async def delete_by_item_code_batch(self, item_codes: List[str]) -> int:
        """
        Массово удаляет шаблоны по списку item_code в рамках переданной сессии.
        """
        if not item_codes:
            logger.info("Пустой список item_codes для массового удаления. Ничего не сделано.")
            return 0

        # Используем оператор in_() для удаления нескольких записей одним запросом
        stmt = delete(EquipmentTemplate).where(EquipmentTemplate.item_code.in_(item_codes))
        result = await self._session.execute(stmt)
        deleted_count = result.rowcount
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Массовое удаление шаблонов завершено. Удалено {deleted_count} записей в сессии.")
        return deleted_count

    async def upsert(self, data: Dict[str, Any]) -> EquipmentTemplate:
        """
        Создает или обновляет шаблон в рамках переданной сессии. Если шаблон с данным item_code существует,
        он обновляется; иначе создается новый.
        """
        item_code = data.get("item_code")
        if not item_code:
            raise ValueError("Item code must be provided for upsert operation.")

        insert_stmt = pg_insert(EquipmentTemplate).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EquipmentTemplate.item_code],
            set_={
                "display_name": insert_stmt.excluded.display_name,
                "category": insert_stmt.excluded.category,
                "sub_category": insert_stmt.excluded.sub_category,
                "equip_slot": insert_stmt.excluded.equip_slot,
                "inventory_size": insert_stmt.excluded.inventory_size,
                "material_code": insert_stmt.excluded.material_code,
                "suffix_code": insert_stmt.excluded.suffix_code,
                "base_modifiers_json": insert_stmt.excluded.base_modifiers_json,
                "quality_tier": insert_stmt.excluded.quality_tier,
                "rarity_level": insert_stmt.excluded.rarity_level,
                "icon_url": insert_stmt.excluded.icon_url,
                "description": insert_stmt.excluded.description,
            }
        ).returning(EquipmentTemplate)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_template = result.scalar_one_or_none()
        if not upserted_template:
            raise RuntimeError("UPSERT шаблона не вернул объект.")
        logger.info(f"Шаблон '{item_code}' успешно добавлен/обновлен в сессии.")
        return upserted_template

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет шаблоны в рамках переданной сессии.
        Если шаблон с данным item_code существует, он обновляется; иначе создается новый.
        """
        if not data_list:
            logger.info("Пустой список данных для upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = {
            k: pg_insert(EquipmentTemplate).excluded[k]
            for k in EquipmentTemplate.__table__.columns.keys()
            if k not in ['item_code']
        }

        insert_stmt = pg_insert(EquipmentTemplate).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EquipmentTemplate.item_code],
            set_=updatable_fields
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} шаблонов предметов в сессии.")
        return upserted_count
