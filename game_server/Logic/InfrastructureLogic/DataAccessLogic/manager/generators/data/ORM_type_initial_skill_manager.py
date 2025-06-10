from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert # Добавил insert
from sqlalchemy.dialects.postgresql import insert as pg_insert # Специфично для PostgreSQL

from game_server.database.models.models import CreatureTypeInitialSkill


class CreatureTypeInitialSkillManager:
    """
    Менеджер для управления объектами CreatureTypeInitialSkill в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_initial_skill(self, creature_type_id: int, skill_key: str) -> Optional[CreatureTypeInitialSkill]:
        """
        Получает запись о начальном навыке для конкретного типа существа и навыка.
        """
        stmt = select(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id,
            CreatureTypeInitialSkill.skill_key == skill_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_initial_skills_for_creature_type(self, creature_type_id: int) -> List[CreatureTypeInitialSkill]:
        """
        Получает все начальные навыки для заданного типа существа.
        """
        stmt = select(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def upsert_initial_skill(self, initial_skill_data: Dict[str, Any]) -> CreatureTypeInitialSkill:
        """
        Создает или обновляет запись CreatureTypeInitialSkill, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Конфликт определяется по составному ключу (creature_type_id, skill_key).

        Args:
            initial_skill_data (Dict[str, Any]): Словарь с данными для создания/обновления начального навыка.
                                                Должен содержать 'creature_type_id' и 'skill_key' для идентификации.

        Returns:
            CreatureTypeInitialSkill: Созданный или обновленный объект CreatureTypeInitialSkill.
        """
        insert_stmt = pg_insert(CreatureTypeInitialSkill).values(**initial_skill_data)
        
        # Определяем конфликт по составному ключу: creature_type_id и skill_key
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[CreatureTypeInitialSkill.creature_type_id, CreatureTypeInitialSkill.skill_key],
            set_={
                "initial_level": insert_stmt.excluded.initial_level,
                # Если есть другие поля, которые нужно обновлять, добавьте их здесь
            }
        ).returning(CreatureTypeInitialSkill)

        result = await self.db.execute(on_conflict_stmt)
        await self.db.commit()
        
        return result.scalar_one() # Используем scalar_one, так как upsert всегда возвращает одну строку

    async def delete_initial_skill(self, creature_type_id: int, skill_key: str) -> bool:
        """
        Удаляет запись о начальном навыке.
        Использует delete-statement для более эффективного удаления.
        """
        stmt = delete(CreatureTypeInitialSkill).where(
            CreatureTypeInitialSkill.creature_type_id == creature_type_id,
            CreatureTypeInitialSkill.skill_key == skill_key
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.rowcount > 0