# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/static_item_template_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Type # ДОБАВЛЕНО Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound # ДОБАВЛЕНО NoResultFound
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IStaticItemTemplateRepository
from game_server.database.models.models import StaticItemTemplate

from game_server.config.logging.logging_setup import app_logger as logger


class StaticItemTemplateRepositoryImpl(IStaticItemTemplateRepository):
    """
    Репозиторий для управления объектами StaticItemTemplate в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> StaticItemTemplate: # ИЗМЕНЕНО: Унифицированное имя
        """
        Создает новый шаблон статического предмета.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            new_template = StaticItemTemplate(**data)
            session.add(new_template)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Шаблон статического предмета '{new_template.item_code}' создан.")
                return new_template
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании шаблона '{data.get('item_code', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Шаблон с таким кодом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании шаблона '{data.get('item_code', 'N/A')}': {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[StaticItemTemplate]: # ИЗМЕНЕНО: Унифицированное имя
        """
        Получает шаблон по его ID.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(StaticItemTemplate).where(StaticItemTemplate.template_id == id)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_by_item_code(self, item_code: str) -> Optional[StaticItemTemplate]:
        """
        Получает шаблон по его item_code.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(StaticItemTemplate).where(StaticItemTemplate.item_code == item_code)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_all(self) -> List[StaticItemTemplate]: # ИЗМЕНЕНО: Унифицированное имя
        """
        Получает все шаблоны статических предметов.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(StaticItemTemplate)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[StaticItemTemplate]: # ИЗМЕНЕНО: Унифицированное имя
        """
        Обновляет существующий шаблон по его ID.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = update(StaticItemTemplate).where(StaticItemTemplate.template_id == id).values(**updates).returning(StaticItemTemplate)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            updated_template = result.scalars().first()
            if updated_template:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Шаблон (ID: {id}) обновлен.")
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Шаблон с ID {id} не найден для обновления.")
            return updated_template

    async def delete(self, id: int) -> bool: # ИЗМЕНЕНО: Унифицированное имя
        """
        Удаляет шаблон по его ID.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = delete(StaticItemTemplate).where(StaticItemTemplate.template_id == id)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Шаблон (ID: {id}) удален.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"Шаблон с ID {id} не найден для удаления.")
                return False

    async def delete_by_item_code_batch(self, item_codes: List[str]) -> int: # Сохраняем специфический метод
        """
        Массово удаляет шаблоны по списку item_code.
        """
        if not item_codes:
            return 0
        async with await self._get_session() as session:
            try:
                stmt = delete(StaticItemTemplate).where(StaticItemTemplate.item_code.in_(item_codes))
                result = await session.execute(stmt)
                await session.commit()
                logger.info(f"Удалено {result.rowcount} статических шаблонов по item_code.")
                return result.rowcount
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка при массовом удалении статических шаблонов: {e}", exc_info=True)
                raise


    async def upsert(self, data: Dict[str, Any]) -> StaticItemTemplate: # ИЗМЕНЕНО: Унифицированное имя
        """
        Создает или обновляет шаблон. Если шаблон с данным item_code существует,
        он обновляется; иначе создается новый.
        """
        item_code = data.get("item_code")
        if not item_code:
            raise ValueError("Item code must be provided for upsert operation.")

        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
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

                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.commit() # ДОБАВЛЕНО commit

                upserted_template = result.scalar_one_or_none()
                if not upserted_template:
                    raise RuntimeError("UPSERT шаблона не вернул объект.")
                logger.info(f"Шаблон '{item_code}' успешно добавлен/обновлен.")
                return upserted_template
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT шаблона '{item_code}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении шаблона: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT шаблона '{item_code}': {e}", exc_info=True)
                raise
    
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # ДОБАВЛЕНО: Унифицированное имя
        """Массово создает или обновляет статические шаблоны."""
        if not data_list:
            logger.info("Пустой список данных для StaticItemTemplate upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} статических шаблонов.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT статических шаблонов: {e}", exc_info=True)
                raise