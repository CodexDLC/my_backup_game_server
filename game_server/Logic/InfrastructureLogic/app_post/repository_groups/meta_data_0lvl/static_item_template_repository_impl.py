# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/static_item_template_repository_impl.py

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IStaticItemTemplateRepository
from game_server.database.models.models import StaticItemTemplate

from game_server.config.logging.logging_setup import app_logger as logger


class StaticItemTemplateRepositoryImpl(IStaticItemTemplateRepository):
    """
    Репозиторий для управления объектами StaticItemTemplate в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> StaticItemTemplate:
        """
        Создает новый шаблон статического предмета в рамках переданной сессии.
        """
        new_template = StaticItemTemplate(**data)
        self._session.add(new_template)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Шаблон статического предмета '{new_template.item_code}' добавлен в сессию.")
        return new_template

    async def get_by_id(self, id: int) -> Optional[StaticItemTemplate]:
        """
        Получает шаблон по его ID в рамках переданной сессии.
        """
        stmt = fselect(StaticItemTemplate).where(StaticItemTemplate.template_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_item_code(self, item_code: str) -> Optional[StaticItemTemplate]:
        """
        Получает шаблон по его item_code в рамках переданной сессии.
        """
        stmt = fselect(StaticItemTemplate).where(StaticItemTemplate.item_code == item_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[StaticItemTemplate]:
        """
        Получает все шаблоны статических предметов из базы данных в рамках переданной сессии.
        """
        stmt = fselect(StaticItemTemplate)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[StaticItemTemplate]:
        """
        Обновляет существующий шаблон по его ID в рамках переданной сессии.
        """
        stmt = update(StaticItemTemplate).where(StaticItemTemplate.template_id == id).values(**updates).returning(StaticItemTemplate)
        result = await self._session.execute(stmt)
        updated_template = result.scalars().first()
        if updated_template:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шаблон (ID: {id}) обновлен в сессии.")
        else:
            logger.warning(f"Шаблон с ID {id} не найден для обновления.")
        return updated_template

    async def delete(self, id: int) -> bool:
        """
        Удаляет шаблон по его ID в рамках переданной сессии.
        """
        stmt = delete(StaticItemTemplate).where(StaticItemTemplate.template_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Шаблон (ID: {id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Шаблон с ID {id} не найден для удаления.")
            return False

    async def delete_by_item_code_batch(self, item_codes: List[str]) -> int:
        """
        Массово удаляет шаблоны по списку item_code в рамках переданной сессии.
        """
        if not item_codes:
            return 0
        stmt = delete(StaticItemTemplate).where(StaticItemTemplate.item_code.in_(item_codes))
        result = await self._session.execute(stmt)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Удалено {result.rowcount} статических шаблонов по item_code в сессии.")
        return result.rowcount

    async def upsert(self, data: Dict[str, Any]) -> StaticItemTemplate:
        """
        Создает или обновляет шаблон в рамках переданной сессии. Если шаблон с данным item_code существует,
        он обновляется; иначе создается новый.
        """
        item_code = data.get("item_code")
        if not item_code:
            raise ValueError("Item code must be provided for upsert operation.")

        insert_stmt = pg_insert(StaticItemTemplate).values(**data)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[StaticItemTemplate.item_code],
            set_={
                "display_name": insert_stmt.excluded.display_name,
                "category": insert_stmt.excluded.category,
                "sub_category": insert_stmt.excluded.sub_category,
                "inventory_size": insert_stmt.excluded.inventory_size,
                "stackable": insert_stmt.excluded.stackable,
                "max_stack_size": insert_stmt.excluded.max_stack_size,
                "base_value": insert_stmt.excluded.base_value,
                "icon_url": insert_stmt.excluded.icon_url,
                "description": insert_stmt.excluded.description,
                "properties_json": insert_stmt.excluded.properties_json,
            }
        ).returning(StaticItemTemplate)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_template = result.scalar_one_or_none()
        if not upserted_template:
            raise RuntimeError("UPSERT шаблона не вернул объект.")
        logger.info(f"Шаблон '{item_code}' успешно добавлен/обновлен в сессии.")
        return upserted_template

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет статические шаблоны в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для StaticItemTemplate upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "display_name", "category", "sub_category", "inventory_size",
            "stackable", "max_stack_size", "base_value", "icon_url",
            "description", "properties_json",
        ]
        set_clause = {field: getattr(pg_insert(StaticItemTemplate).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(StaticItemTemplate).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[StaticItemTemplate.item_code],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} статических шаблонов в сессии.")
        return upserted_count
