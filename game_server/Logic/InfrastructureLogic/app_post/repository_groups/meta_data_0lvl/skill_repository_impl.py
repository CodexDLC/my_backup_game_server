# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Type # ДОБАВЛЕНО Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, NoResultFound # ДОБАВЛЕНО NoResultFound

from game_server.database.models.models import Skills

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ISkillRepository

from game_server.config.logging.logging_setup import app_logger as logger


class SkillRepositoryImpl(ISkillRepository):
    """
    Репозиторий для управления объектами Skill в базе данных (асинхронный).
    """
    def __init__(self, db_session_factory: Type[AsyncSession]): # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> Skills: # РЕАЛИЗУЕТ: IAbilityRepository.create
        """Создает новый навык."""
        async with await self._get_session() as session:
            new_skill = Skills(**data)
            session.add(new_skill)
            try:
                await session.flush()
                await session.commit()
                logger.info(f"Навык '{new_skill.name}' (Key: {new_skill.skill_key}) создан.")
                return new_skill
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании навыка '{data.get('skill_key', 'N/A')}': {e.orig}", exc_info=True)
                raise ValueError(f"Навык с таким ключом уже существует.")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании навыка: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: str) -> Optional[Skills]: # РЕАЛИЗУЕТ: ISkillRepository.get_by_id (PK - skill_key: str)
        """Получает определение навыка по его строковому ключу (который является PK)."""
        return await self.get_skill_by_key(id) # Вызываем существующий специфичный метод

    async def get_by_key(self, skill_key: str) -> Optional[Skills]: # СПЕЦИФИЧЕСКИЙ МЕТОД, ВЫЗЫВАЕТСЯ ИЗ get_by_id
        """Получает определение навыка по его строковому ключу."""
        async with await self._get_session() as session:
            stmt = fselect(Skills).where(Skills.skill_key == skill_key)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_skill_by_id(self, skill_id: int) -> Optional[Skills]: # СПЕЦИФИЧЕСКИЙ МЕТОД, РЕАЛИЗУЕТ: ISkillRepository.get_skill_by_id
        """Получает определение навыка по его ID (skill_id не является PK)."""
        async with await self._get_session() as session:
            stmt = fselect(Skills).where(Skills.skill_id == skill_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def get_all(self) -> List[Skills]: # РЕАЛИЗУЕТ: ISkillRepository.get_all
        """Возвращает все навыки."""
        return await self.get_all_skills() # Вызываем существующий специфичный метод

    async def get_all_skills(self) -> List[Skills]: # СПЕЦИФИЧЕСКИЙ МЕТОД, РЕАЛИЗУЕТ: ISkillRepository.get_all_skills
        """Возвращает все навыки."""
        async with await self._get_session() as session:
            stmt = fselect(Skills)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Skills]: # РЕАЛИЗУЕТ: ISkillRepository.update
        """Обновляет существующий навык по его строковому ключу (skill_key)."""
        async with await self._get_session() as session:
            stmt = update(Skills).where(Skills.skill_key == id).values(**updates).returning(Skills)
            result = await session.execute(stmt)
            updated_skill = result.scalars().first()
            if updated_skill:
                await session.flush()
                await session.commit()
                logger.info(f"Навык '{id}' обновлен.")
            else:
                await session.rollback()
                logger.warning(f"Навык с ключом '{id}' не найден для обновления.")
            return updated_skill

    async def delete(self, id: str) -> bool: # РЕАЛИЗУЕТ: ISkillRepository.delete
        """Удаляет навык по его строковому ключу (skill_key)."""
        return await self.delete_skill(id) # Вызываем существующий специфичный метод

    async def delete_skill(self, skill_key: str) -> bool: # СПЕЦИФИЧЕСКИЙ МЕТОД, РЕАЛИЗУЕТ: ISkillRepository.delete_skill
        """Удаляет навык по его строковому ключу."""
        async with await self._get_session() as session:
            stmt = delete(Skills).where(Skills.skill_key == skill_key)
            result = await session.execute(stmt)
            if result.rowcount > 0:
                await session.flush()
                await session.commit()
                logger.info(f"Навык '{skill_key}' удален.")
                return True
            else:
                await session.rollback()
                logger.warning(f"Навык '{skill_key}' не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> Skills: # РЕАЛИЗУЕТ: ISkillRepository.upsert
        """Создает или обновляет запись Skill, используя upsert (INSERT ON CONFLICT DO UPDATE)."""
        return await self.upsert_skill(data) # Вызываем существующий специфичный метод

    async def upsert_skill(self, skill_data: Dict[str, Any]) -> Skills: # СПЕЦИФИЧЕСКИЙ МЕТОД, РЕАЛИЗУЕТ: ISkillRepository.upsert_skill
        """
        Создает или обновляет запись Skill, используя upsert (INSERT ON CONFLICT DO UPDATE).
        """
        skill_key = skill_data.get("skill_key")
        if not skill_key:
            raise ValueError("Skill key must be provided for upsert operation.")

        async with await self._get_session() as session:
            try:
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

                result = await session.execute(on_conflict_stmt)
                await session.flush()
                await session.commit()

                upserted_skill = result.scalar_one_or_none()
                if not upserted_skill:
                    raise RuntimeError("UPSERT навыка не вернул объект.")
                logger.info(f"Навык '{upserted_skill.name}' (Key: {upserted_skill.skill_key}) успешно добавлен/обновлен.")
                return upserted_skill
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT навыка '{skill_key}': {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении навыка: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT навыка '{skill_key}': {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: # РЕАЛИЗУЕТ: ISkillRepository.upsert_many
        """Массово создает или обновляет навыки."""
        if not data_list:
            logger.info("Пустой список данных для Skills upsert_many. Ничего не сделано.")
            return 0

        upserted_count = 0
        async with await self._get_session() as session:
            try:
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
                
                result = await session.execute(on_conflict_stmt)
                await session.commit()
                upserted_count = result.rowcount
                logger.info(f"Успешно массово добавлено/обновлено {upserted_count} навыков.")
                return upserted_count
            except Exception as e:
                await session.rollback()
                logger.error(f"Критическая ошибка при массовом UPSERT навыков: {e}", exc_info=True)