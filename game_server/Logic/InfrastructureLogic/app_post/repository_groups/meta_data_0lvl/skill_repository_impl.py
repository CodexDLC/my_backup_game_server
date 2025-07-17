# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import Skills

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ISkillRepository

from game_server.config.logging.logging_setup import app_logger as logger


class SkillRepositoryImpl(ISkillRepository):
    """
    Репозиторий для управления объектами Skill в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> Skills:
        """Создает новый навык в рамках переданной сессии."""
        new_skill = Skills(**data)
        self._session.add(new_skill)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Навык '{new_skill.name}' (Key: {new_skill.skill_key}) добавлен в сессию.")
        return new_skill

    async def get_by_id(self, id: str) -> Optional[Skills]:
        """Получает определение навыка по его строковому ключу (который является PK) в рамках переданной сессии."""
        return await self.get_skill_by_key(id) # Вызываем существующий специфичный метод

    async def get_by_key(self, skill_key: str) -> Optional[Skills]:
        """Получает определение навыка по его строковому ключу в рамках переданной сессии."""
        stmt = fselect(Skills).where(Skills.skill_key == skill_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_skill_by_id(self, skill_id: int) -> Optional[Skills]:
        """Получает определение навыка по его ID (skill_id не является PK) в рамках переданной сессии."""
        stmt = fselect(Skills).where(Skills.skill_id == skill_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Skills]:
        """Возвращает все навыки из базы данных в рамках переданной сессии."""
        return await self.get_all_skills() # Вызываем существующий специфичный метод

    async def get_all_skills(self) -> List[Skills]:
        """Возвращает все навыки из базы данных в рамках переданной сессии."""
        stmt = fselect(Skills)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Skills]:
        """Обновляет существующий навык по его строковому ключу (skill_key) в рамках переданной сессии."""
        stmt = update(Skills).where(Skills.skill_key == id).values(**updates).returning(Skills)
        result = await self._session.execute(stmt)
        updated_skill = result.scalars().first()
        if updated_skill:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Навык '{id}' обновлен в сессии.")
        else:
            logger.warning(f"Навык с ключом '{id}' не найден для обновления.")
        return updated_skill

    async def delete(self, id: str) -> bool:
        """Удаляет навык по его строковому ключу (skill_key) в рамках переданной сессии."""
        return await self.delete_skill(id) # Вызываем существующий специфичный метод

    async def delete_skill(self, skill_key: str) -> bool:
        """Удаляет навык по его строковому ключу в рамках переданной сессии."""
        stmt = delete(Skills).where(Skills.skill_key == skill_key)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Навык '{skill_key}' помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Навык '{skill_key}' не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> Skills:
        """Создает или обновляет запись Skill, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии."""
        return await self.upsert_skill(data) # Вызываем существующий специфичный метод

    async def upsert_skill(self, skill_data: Dict[str, Any]) -> Skills:
        """
        Создает или обновляет запись Skill, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии.
        """
        skill_key = skill_data.get("skill_key")
        if not skill_key:
            raise ValueError("Skill key must be provided for upsert operation.")

        insert_stmt = pg_insert(Skills).values(**skill_data)

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Skills.skill_key],
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description,
                "stat_influence": insert_stmt.excluded.stat_influence,
                "is_magic": insert_stmt.excluded.is_magic,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
                "category_tag": insert_stmt.excluded.category_tag,
                "role_preference_tag": insert_stmt.excluded.role_preference_tag,
                "limit_group_tag": insert_stmt.excluded.limit_group_tag,
                "max_level": insert_stmt.excluded.max_level,
            }
        ).returning(Skills)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_skill = result.scalar_one_or_none()
        if not upserted_skill:
            raise RuntimeError("UPSERT навыка не вернул объект.")
        logger.info(f"Навык '{upserted_skill.name}' (Key: {upserted_skill.skill_key}) успешно добавлен/обновлен в сессии.")
        return upserted_skill

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """Массово создает или обновляет навыки в рамках переданной сессии."""
        if not data_list:
            logger.info("Пустой список данных для Skills upsert_many. Ничего не сделано.")
            return 0

        updatable_fields = [
            "name", "description", "stat_influence", "is_magic",
            "rarity_weight", "category_tag", "role_preference_tag",
            "limit_group_tag", "max_level",
        ]
        set_clause = {field: getattr(pg_insert(Skills).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(Skills).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Skills.skill_key],
            set_=set_clause
        )

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        upserted_count = result.rowcount
        logger.info(f"Успешно массово добавлено/обновлено {upserted_count} навыков в сессии.")
        return upserted_count
