# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/creature_type_initial_skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Tuple, Type # Добавлен Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, NoResultFound

from game_server.database.models.models import CreatureTypeInitialSkill

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeInitialSkillRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class CreatureTypeInitialSkillRepositoryImpl(ICreatureTypeInitialSkillRepository):
    """
    Репозиторий для управления объектами CreatureTypeInitialSkill в базе данных (асинхронный).
    """
    # ИЗМЕНЕНО: Конструктор теперь принимает db_session_factory
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

    async def _get_session(self) -> AsyncSession:
        """Вспомогательный метод для получения сессии из фабрики."""
        # Асинхронный контекстный менеджер для sessionmaker
        return self._db_session_factory()

    async def create(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill:
        """
        Создает новую запись CreatureTypeInitialSkill.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО: Использование async with
            new_skill = CreatureTypeInitialSkill(**data)
            session.add(new_skill)
            try:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"Создан новый CreatureTypeInitialSkill: {new_skill.creature_type_id}, {new_skill.skill_key}")
                return new_skill
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при создании CreatureTypeInitialSkill: {e.orig}", exc_info=True)
                raise ValueError(f"Запись с таким ID уже существует или нарушение других ограничений: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при создании CreatureTypeInitialSkill: {e}", exc_info=True)
                raise

    async def get_by_id(self, id: Tuple[int, str]) -> Optional[CreatureTypeInitialSkill]:
        """
        Получает запись CreatureTypeInitialSkill по составному PK (creature_type_id, skill_key).
        """
        creature_type_id, skill_key = id
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(CreatureTypeInitialSkill).where(
                CreatureTypeInitialSkill.creature_type_id == creature_type_id,
                CreatureTypeInitialSkill.skill_key == skill_key
            )
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return result.scalar_one_or_none()

    async def get_all(self) -> List[CreatureTypeInitialSkill]:
        """
        Получает все записи CreatureTypeInitialSkill.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(CreatureTypeInitialSkill)
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def update(self, id: Tuple[int, str], updates: Dict[str, Any]) -> Optional[CreatureTypeInitialSkill]:
        """
        Обновляет запись CreatureTypeInitialSkill по составному PK.
        """
        creature_type_id, skill_key = id
        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
                stmt = update(CreatureTypeInitialSkill).where(
                    CreatureTypeInitialSkill.creature_type_id == creature_type_id,
                    CreatureTypeInitialSkill.skill_key == skill_key
                ).values(**updates).returning(CreatureTypeInitialSkill)
                result = await session.execute(stmt) # ИЗМЕНЕНО
                updated_skill = result.scalar_one_or_none()
                if updated_skill:
                    await session.flush()
                    await session.commit() # ДОБАВЛЕНО commit
                    logger.info(f"Обновлен CreatureTypeInitialSkill с ID {id}.")
                else:
                    await session.rollback() # ДОБАВЛЕНО rollback
                    logger.warning(f"CreatureTypeInitialSkill с ID {id} не найден для обновления.")
                return updated_skill
            except Exception as e:
                await session.rollback()
                logger.error(f"Ошибка при обновлении CreatureTypeInitialSkill с ID {id}: {e}", exc_info=True)
                raise

    async def delete(self, id: Tuple[int, str]) -> bool:
        """
        Удаляет запись CreatureTypeInitialSkill по составному PK.
        Это унифицированный метод удаления.
        """
        creature_type_id, skill_key = id
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = delete(CreatureTypeInitialSkill).where(
                CreatureTypeInitialSkill.creature_type_id == creature_type_id,
                CreatureTypeInitialSkill.skill_key == skill_key
            )
            result = await session.execute(stmt) # ИЗМЕНЕНО
            if result.rowcount > 0:
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit
                logger.info(f"CreatureTypeInitialSkill с ID {id} помечен для удаления в сессии.")
                return True
            else:
                await session.rollback() # ДОБАВЛЕНО rollback
                logger.warning(f"CreatureTypeInitialSkill с ID {id} не найден для удаления.")
                return False

    async def upsert(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill:
        """
        Создает или обновляет запись CreatureTypeInitialSkill, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Унифицированная версия метода.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
                insert_stmt = pg_insert(CreatureTypeInitialSkill).values(**data)

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CreatureTypeInitialSkill.creature_type_id, CreatureTypeInitialSkill.skill_key],
                    set_={
                        "initial_level": insert_stmt.excluded.initial_level,
                        **{k: insert_stmt.excluded[k] for k in data if k not in ['creature_type_id', 'skill_key']}
                    }
                ).returning(CreatureTypeInitialSkill)

                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.flush()
                await session.commit() # ДОБАВЛЕНО commit

                upserted_skill = result.scalar_one_or_none()
                if not upserted_skill:
                    raise RuntimeError("UPSERT CreatureTypeInitialSkill не вернул объект.")
                logger.info(f"CreatureTypeInitialSkill с ID ({data.get('creature_type_id', 'N/A')}, {data.get('skill_key', 'N/A')}) успешно добавлен/обновлен в сессии.")
                return upserted_skill
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при UPSERT CreatureTypeInitialSkill: {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при сохранении CreatureTypeInitialSkill: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при UPSERT CreatureTypeInitialSkill: {e}", exc_info=True)
                raise

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет записи CreatureTypeInitialSkill.
        Возвращает количество затронутых строк.
        """
        if not data_list:
            return 0

        async with await self._get_session() as session: # ИЗМЕНЕНО
            try:
                insert_stmt = pg_insert(CreatureTypeInitialSkill).values(data_list)
                
                updatable_fields = {
                    k: insert_stmt.excluded[k]
                    for k in CreatureTypeInitialSkill.__table__.columns.keys()
                    if k not in ['creature_type_id', 'skill_key']
                }

                on_conflict_stmt = insert_stmt.on_conflict_do_update(
                    index_elements=[CreatureTypeInitialSkill.creature_type_id, CreatureTypeInitialSkill.skill_key],
                    set_=updatable_fields
                )
                
                result = await session.execute(on_conflict_stmt) # ИЗМЕНЕНО
                await session.commit() # ДОБАВЛЕНО commit
                affected_rows = result.rowcount
                logger.info(f"Массовый upsert CreatureTypeInitialSkill затронул {affected_rows} строк.")
                return affected_rows
            except IntegrityError as e:
                await session.rollback()
                logger.error(f"Ошибка целостности при массовом UPSERT CreatureTypeInitialSkill: {e.orig}", exc_info=True)
                raise ValueError(f"Ошибка целостности при массовом сохранении CreatureTypeInitialSkill: {e.orig}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Непредвиденная ошибка при массовом UPSERT CreatureTypeInitialSkill: {e}", exc_info=True)
                raise

    async def get_initial_skill(self, creature_type_id: int, skill_key: str) -> Optional[CreatureTypeInitialSkill]:
        """
        Получает запись о начальном навыке для конкретного типа существа и навыка.
        Этот метод дублирует функционал get_by_id, но сохраняется для специфического использования.
        """
        return await self.get_by_id((creature_type_id, skill_key))

    async def get_initial_skills_for_creature_type(self, creature_type_id: int) -> List[CreatureTypeInitialSkill]:
        """
        Получает все начальные навыки для заданного типа существа.
        """
        async with await self._get_session() as session: # ИЗМЕНЕНО
            stmt = fselect(CreatureTypeInitialSkill).where(
                CreatureTypeInitialSkill.creature_type_id == creature_type_id
            )
            result = await session.execute(stmt) # ИЗМЕНЕНО
            return list(result.scalars().all())

    async def delete_initial_skill(self, creature_type_id: int, skill_key: str) -> bool:
        """
        Удаляет запись о начальном навыке по creature_type_id и skill_key.
        Это специфический метод удаления, который удобно использовать для удаления по двум ключам.
        """
        return await self.delete((creature_type_id, skill_key))