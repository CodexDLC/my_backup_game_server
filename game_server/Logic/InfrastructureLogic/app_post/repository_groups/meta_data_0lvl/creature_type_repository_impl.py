# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/creature_type_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from game_server.database.models.models import CreatureType, CreatureTypeInitialSkill

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeRepository

from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class CreatureTypeRepositoryImpl(ICreatureTypeRepository):
    """
    Репозиторий для управления объектами CreatureType в базе данных (асинхронный).
    """
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> CreatureType:
        """Создает новую запись типа существа."""
        async with await self._get_session() as session:
            new_creature_type = CreatureType(**data)
            session.add(new_creature_type)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Тип существа '{new_creature_type.name}' (ID: {new_creature_type.creature_type_id}) создан.")
                return new_creature_type
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании типа существа '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Тип существа с таким именем или ID уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании типа существа: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: int) -> Optional[CreatureType]: # Унифицированное имя
        """Получает тип существа по его ID."""
        async with await self._get_session() as session:
            stmt = fselect(CreatureType).where(CreatureType.creature_type_id == id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[CreatureType]:
        """Получает тип существа по его имени (name)."""
        async with await self._get_session() as session:
            stmt = fselect(CreatureType).where(CreatureType.name == name)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[CreatureType]:
        """Получает все типы существ из базы данных."""
        async with await self._get_session() as session:
            stmt = fselect(CreatureType)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[CreatureType]: # Унифицированное имя
        """Обновляет существующий тип существа по ID."""
        async with await self._get_session() as session:
            stmt = update(CreatureType).where(CreatureType.creature_type_id == id).values(**updates).returning(CreatureType)
            result = await session.execute(stmt)
            updated_creature_type = result.scalars().first()
            if updated_creature_type:
                await session.flush()
                await session.commit()
                logger.info(f"Тип существа (ID: {id}) обновлен.")
            else:
                await session.rollback()
                logger.warning(f"Тип существа с ID {id} не найден для обновления.")
            return updated_creature_type

    async def delete(self, id: int) -> bool: # Унифицированное имя
        """Удаляет тип существа по его ID."""
        async with await self._get_session() as session:
            stmt = delete(CreatureType).where(CreatureType.creature_type_id == id)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Тип существа (ID: {id}) удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Тип существа (ID: {id}) не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> CreatureType: # Унифицированное имя
        """Создает или обновляет тип существа, используя UPSERT."""
        creature_type_id = data.get("creature_type_id")
        if creature_type_id is None:
            raise ValueError("Creature type ID must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
                insert_stmt = pg_insert(CreatureType).values(**data)

                update_cols = {k: insert_stmt.excluded[k] for k in data if k != 'creature_type_id'} # Обновляем все, кроме PK

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CreatureType.creature_type_id],
                    set_=update_cols
                ).returning(CreatureType)

                result = await session.execute(on_conflict_stmt)
                await session.flush()
                await session.commit()

                new_creature_type = result.scalar_one_or_none()
                if not new_creature_type:
                    raise RuntimeError("UPSERT не вернул объект.")
                logger.info(f"Тип существа '{new_creature_type.name}' (ID: {new_creature_type.creature_type_id}) успешно добавлен/обновлен.")
                return new_creature_type
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT типа существа '{data.get('name', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении типа существа: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT типа существа '{data.get('name', 'N/A')}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # Добавлен
        """Массово создает или обновляет типы существ."""
        if not data_list:
            logger.info("Пустой список данных для CreatureType upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
                updatable_fields = [
                    "name", "description", "category", "subcategory",
                    "visual_tags", "rarity_weight", "is_playable",
                ]
                set_clause = {field: getattr(pg_insert(CreatureType).excluded, field) for field in updatable_fields}

                insert_stmt = pg_insert(CreatureType).values(data_list)
                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CreatureType.creature_type_id],
                    set_=set_clause
                )
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} типов существ.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT типов существ: {e}", exc_info=True)
                raise


    async def delete_by_id(self, id: int) -> bool: # Добавлен, если ожидается интерфейсом (для унификации)
        return await self.delete(id) # Вызываем основной метод удаления


    async def get_filtered_by_category_and_playable(self, category: str, is_playable: bool) -> List[CreatureType]:
        """
        Получает отфильтрованные типы существ по категории и флагу is_playable.
        """
        async with await self._get_session() as session:
            stmt = fselect(CreatureType).where(
                CreatureType.category == category,
                CreatureType.is_playable == is_playable
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_creature_type_with_initial_skills(self, creature_type_id: int) -> Optional[CreatureType]:
        """
        Получает тип существа вместе с его начальными навыками.
        Использует selectinload для оптимизированной загрузки связанных данных.
        """
        async with await self._get_session() as session:
            stmt = fselect(CreatureType).where(CreatureType.creature_type_id == creature_type_id).options(
                selectinload(CreatureType.initial_skills).selectinload(CreatureTypeInitialSkill.skill_definition)
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()