# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/creature_type_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from game_server.database.models.models import CreatureType, CreatureTypeInitialSkill

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeRepository

from game_server.config.logging.logging_setup import app_logger as logger


class CreatureTypeRepositoryImpl(ICreatureTypeRepository):
    """
    Репозиторий для управления объектами CreatureType в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> CreatureType:
        """Создает новую запись типа существа в рамках переданной сессии."""
        new_creature_type = CreatureType(**data)
        self._session.add(new_creature_type)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Тип существа '{new_creature_type.name}' (ID: {new_creature_type.creature_type_id}) добавлен в сессию.")
        return new_creature_type

    async def get_by_id(self, id: int) -> Optional[CreatureType]:
        """Получает тип существа по его ID в рамках переданной сессии."""
        stmt = fselect(CreatureType).where(CreatureType.creature_type_id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[CreatureType]:
        """Получает тип существа по его имени (name) в рамках переданной сессии."""
        stmt = fselect(CreatureType).where(CreatureType.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[CreatureType]:
        """Получает все типы существ из базы данных в рамках переданной сессии."""
        stmt = fselect(CreatureType)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[CreatureType]:
        """Обновляет существующий тип существа по ID в рамках переданной сессии."""
        stmt = update(CreatureType).where(CreatureType.creature_type_id == id).values(**updates).returning(CreatureType)
        result = await self._session.execute(stmt)
        updated_creature_type = result.scalars().first()
        if updated_creature_type:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Тип существа (ID: {id}) обновлен в сессии.")
        else:
            logger.warning(f"Тип существа с ID {id} не найден для обновления.")
        return updated_creature_type

    async def delete(self, id: int) -> bool:
        """Удаляет тип существа по его ID в рамках переданной сессии."""
        stmt = delete(CreatureType).where(CreatureType.creature_type_id == id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Тип существа (ID: {id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Тип существа (ID: {id}) не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> CreatureType:
        """Создает или обновляет тип существа, используя UPSERT в рамках переданной сессии."""
        creature_type_id = data.get("creature_type_id")
        if creature_type_id is None:
            raise ValueError("Creature type ID must be provided for upsert operation.")

        insert_stmt = pg_insert(CreatureType).values(**data)

        update_cols = {k: insert_stmt.excluded[k] for k in data if k != 'creature_type_id'} # Обновляем все, кроме PK

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[CreatureType.creature_type_id],
            set_=update_cols
        ).returning(CreatureType)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        new_creature_type = result.scalar_one_or_none()
        if not new_creature_type:
            raise RuntimeError("UPSERT не вернул объект.")
        logger.info(f"Тип существа '{new_creature_type.name}' (ID: {new_creature_type.creature_type_id}) успешно добавлен/обновлен в сессии.")
        return new_creature_type

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет типы существ в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для CreatureType upsert_many. Ничего не сделано.")
            return 0

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

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} типов существ в сессии.")
        return upserted_count

    async def delete_by_id(self, id: int) -> bool:
        """Удаляет тип существа по его ID (для унификации) в рамках переданной сессии."""
        return await self.delete(id) # Вызываем основной метод удаления

    async def get_filtered_by_category_and_playable(self, category: str, is_playable: bool) -> List[CreatureType]:
        """
        Получает отфильтрованные типы существ по категории и флагу is_playable в рамках переданной сессии.
        """
        stmt = fselect(CreatureType).where(
            CreatureType.category == category,
            CreatureType.is_playable == is_playable
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_creature_type_with_initial_skills(self, creature_type_id: int) -> Optional[CreatureType]:
        """
        Получает тип существа вместе с его начальными навыками в рамках переданной сессии.
        Использует selectinload для оптимизированной загрузки связанных данных.
        """
        stmt = fselect(CreatureType).where(CreatureType.creature_type_id == creature_type_id).options(
            selectinload(CreatureType.initial_skills).selectinload(CreatureTypeInitialSkill.skill_definition)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
