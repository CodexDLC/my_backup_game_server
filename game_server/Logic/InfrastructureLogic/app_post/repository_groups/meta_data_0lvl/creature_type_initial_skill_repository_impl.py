# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/creature_type_initial_skill_repository_impl.py

import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy.future import select as fselect
from sqlalchemy import delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from game_server.database.models.models import CreatureTypeInitialSkill

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeInitialSkillRepository

# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class CreatureTypeInitialSkillRepositoryImpl(ICreatureTypeInitialSkillRepository):
    """
    Репозиторий для управления объектами CreatureTypeInitialSkill в базе данных (асинхронный).
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill:
        """
        Создает новую запись CreatureTypeInitialSkill в рамках переданной сессии.
        """
        new_skill = CreatureTypeInitialSkill(**data)
        self._session.add(new_skill)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Создан новый CreatureTypeInitialSkill: {new_skill.creature_type_id}, {new_skill.skill_key} в сессии.")
        return new_skill

    async def get_by_id(self, id: Tuple[int, str]) -> Optional[CreatureTypeInitialSkill]:
        """
        Получает запись CreatureTypeInitialSkill по составному PK (creature_type_id, skill_key) в рамках переданной сессии.
        """
        creature_type_id, skill_key = id
        stmt = fselect(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id,
            CreatureTypeInitialSkill.skill_key == skill_key
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> List[CreatureTypeInitialSkill]:
        """
        Получает все записи CreatureTypeInitialSkill из базы данных в рамках переданной сессии.
        """
        stmt = fselect(CreatureTypeInitialSkill)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, id: Tuple[int, str], updates: Dict[str, Any]) -> Optional[CreatureTypeInitialSkill]:
        """
        Обновляет запись CreatureTypeInitialSkill по составному PK в рамках переданной сессии.
        """
        creature_type_id, skill_key = id
        stmt = update(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id,
            CreatureTypeInitialSkill.skill_key == skill_key
        ).values(**updates).returning(CreatureTypeInitialSkill)
        result = await self._session.execute(stmt)
        updated_skill = result.scalars().first()
        if updated_skill:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Обновлен CreatureTypeInitialSkill с ID {id} в сессии.")
        else:
            logger.warning(f"CreatureTypeInitialSkill с ID {id} не найден для обновления.")
        return updated_skill

    async def delete(self, id: Tuple[int, str]) -> bool:
        """
        Удаляет запись CreatureTypeInitialSkill по составному PK в рамках переданной сессии.
        Это унифицированный метод удаления.
        """
        creature_type_id, skill_key = id
        stmt = delete(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id,
            CreatureTypeInitialSkill.skill_key == skill_key
        )
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"CreatureTypeInitialSkill с ID {id} помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"CreatureTypeInitialSkill с ID {id} не найден для удаления.")
            return False

    async def upsert(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill:
        """
        Создает или обновляет запись CreatureTypeInitialSkill, используя upsert (INSERT ON CONFLICT DO UPDATE) в рамках переданной сессии.
        Унифицированная версия метода.
        """
        insert_stmt = pg_insert(CreatureTypeInitialSkill).values(**data)

        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[CreatureTypeInitialSkill.creature_type_id, CreatureTypeInitialSkill.skill_key],
            set_={
                "initial_level": insert_stmt.excluded.initial_level,
                **{k: insert_stmt.excluded[k] for k in data if k not in ['creature_type_id', 'skill_key']}
            }
        ).returning(CreatureTypeInitialSkill)

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit

        upserted_skill = result.scalar_one_or_none()
        if not upserted_skill:
            raise RuntimeError("UPSERT CreatureTypeInitialSkill не вернул объект.")
        logger.info(f"CreatureTypeInitialSkill с ID ({data.get('creature_type_id', 'N/A')}, {data.get('skill_key', 'N/A')}) успешно добавлен/обновлен в сессии.")
        return upserted_skill

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int:
        """
        Массово создает или обновляет записи CreatureTypeInitialSkill в рамках переданной сессии.
        Возвращает количество затронутых строк.
        """
        if not data_list:
            return 0

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

        result = await self._session.execute(on_conflict_stmt)
        await self._session.flush() # flush, но НЕ commit
        affected_rows = result.rowcount
        logger.info(f"Массовый upsert CreatureTypeInitialSkill затронул {affected_rows} строк в сессии.")
        return affected_rows

    async def get_initial_skill(self, creature_type_id: int, skill_key: str) -> Optional[CreatureTypeInitialSkill]:
        """
        Получает запись о начальном навыке для конкретного типа существа и навыка в рамках переданной сессии.
        Этот метод дублирует функционал get_by_id, но сохраняется для специфического использования.
        """
        return await self.get_by_id((creature_type_id, skill_key))

    async def delete_initial_skill(self, creature_type_id: int, skill_key: str) -> bool:
        """
        Удаляет запись о начальном навыке по creature_type_id и skill_key в рамках переданной сессии.
        Это специфический метод удаления, который удобно использовать для удаления по двум ключам.
        """
        return await self.delete((creature_type_id, skill_key))

    async def get_initial_skills_for_creature_type(self, creature_type_id: int) -> List[CreatureTypeInitialSkill]:
        """
        Получает все начальные навыки для указанного типа существа.
        """
        stmt = fselect(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())