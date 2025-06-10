# game_server/Logic/InfrastructureLogic/DataAccessLogic/manager/generators/ORM_skills_manager.py

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert # Специфично для PostgreSQL

from game_server.database.models.models import Skills # Убедитесь, что Skills импортирован из вашего файла моделей


class SkillsManager:
    """
    Менеджер для управления объектами Skill в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session # Исправлено: использование self.session вместо self.db


    async def get_skill_by_key(self, skill_key: str) -> Optional[Skills]:
        """
        Получает определение навыка по его строковому ключу.
        """
        stmt = select(Skills).where(Skills.skill_key == skill_key)
        result = await self.session.execute(stmt) # Исправлено: использование self.session вместо self.db
        return result.scalar_one_or_none()

    async def get_skill_by_id(self, skill_id: int) -> Optional[Skills]:
        """
        Получает определение навыка по его ID.
        """
        stmt = select(Skills).where(Skills.skill_id == skill_id)
        result = await self.session.execute(stmt) # Исправлено: использование self.session вместо self.db
        return result.scalar_one_or_none()

    async def get_all_skills(self) -> List[Skills]:
        """
        Возвращает все навыки.
        """
        stmt = select(Skills)
        result = await self.session.execute(stmt) # Исправлено: использование self.session вместо self.db
        return result.scalars().all()

    async def upsert_skill(self, skill_data: Dict[str, Any]) -> Skills:
        """
        Создает или обновляет запись Skill, используя upsert (INSERT ON CONFLICT DO UPDATE).
        Конфликт определяется по 'skill_key', так как это уникальный идентификатор для навыка.

        Args:
            skill_data (Dict[str, Any]): Словарь с данными для создания/обновления навыка.
                                       Должен содержать 'skill_key' для идентификации.

        Returns:
            Skills: Созданный или обновленный объект Skills.
        """
        insert_stmt = pg_insert(Skills).values(**skill_data)
        
        # Определяем конфликт по 'skill_key'
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Skills.skill_key], # По каким полям определяем конфликт
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description, # Добавлено новое поле
                "stat_influence": insert_stmt.excluded.stat_influence, # Добавлено новое поле
                "is_magic": insert_stmt.excluded.is_magic, # Добавлено новое поле
                "rarity_weight": insert_stmt.excluded.rarity_weight, # Добавлено новое поле
                "category_tag": insert_stmt.excluded.category_tag, # Добавлено новое поле
                "role_preference_tag": insert_stmt.excluded.role_preference_tag, # Добавлено новое поле
                "limit_group_tag": insert_stmt.excluded.limit_group_tag, # Добавлено новое поле
                "max_level": insert_stmt.excluded.max_level,
                # Удалены "skill_group", "main_special", "secondary_special"
            }
        ).returning(Skills) # Возвращаем объект после upsert

        result = await self.session.execute(on_conflict_stmt) # Исправлено: использование self.session вместо self.db
        await self.session.commit() # Исправлено: использование self.session вместо self.db
        
        return result.scalar_one() # Используем scalar_one, так как upsert всегда возвращает одну строку

    async def delete_skill(self, skill_key: str) -> bool:
        """
        Удаляет навык по его строковому ключу.
        Использует delete-statement для более эффективного удаления.
        """
        stmt = delete(Skills).where(Skills.skill_key == skill_key)
        result = await self.session.execute(stmt) # Исправлено: использование self.session вместо self.db
        await self.session.commit() # Исправлено: использование self.session вместо self.db
        return result.rowcount is not None and result.rowcount > 0