from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert # Добавил insert
from sqlalchemy.dialects.postgresql import insert as pg_insert # Специфично для PostgreSQL

from game_server.database.models.models import Bloodline


class BloodlineManager:
    """
    Менеджер для управления объектами Bloodline в базе данных (асинхронный).
    Отвечает за взаимодействие с базой данных на уровне DataAccess.
    """
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_bloodline_by_id(self, bloodline_id: int) -> Optional[Bloodline]:
        """Получает родословную по её ID."""
        stmt = select(Bloodline).where(Bloodline.bloodline_id == bloodline_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_bloodline_by_name(self, name: str) -> Optional[Bloodline]:
        """Получает родословную по её названию."""
        stmt = select(Bloodline).where(Bloodline.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_bloodlines(self) -> List[Bloodline]:
        """Возвращает все родословные."""
        stmt = select(Bloodline)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def upsert_bloodline(self, bloodline_data: Dict[str, Any]) -> Bloodline:
        """
        Создает или обновляет запись Bloodline, используя upsert (INSERT ON CONFLICT DO UPDATE).

        Args:
            bloodline_data (Dict[str, Any]): Словарь с данными для создания/обновления родословной.
                                          Должен содержать 'bloodline_id' для идентификации.

        Returns:
            Bloodline: Созданный или обновленный объект Bloodline.
        """
        insert_stmt = pg_insert(Bloodline).values(**bloodline_data)
        
        # Определяем, какие поля обновлять в случае конфликта (т.е. если запись уже существует)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[Bloodline.bloodline_id], # По каким полям определяем конфликт
            set_={
                "name": insert_stmt.excluded.name,
                "description": insert_stmt.excluded.description,
                "inherent_bonuses": insert_stmt.excluded.inherent_bonuses,
                "rarity_weight": insert_stmt.excluded.rarity_weight,
                "story_fragments": insert_stmt.excluded.story_fragments,
                # Добавьте все поля, которые вы хотите обновлять
            }
        ).returning(Bloodline) # Возвращаем объект после upsert

        result = await self.db.execute(on_conflict_stmt)
        await self.db.commit()
        
        return result.scalar_one() # Используем scalar_one, так как upsert всегда возвращает одну строку

    async def delete_bloodline(self, bloodline_id: int) -> bool:
        """
        Удаляет родословную по её ID.
        Использует delete-statement для более эффективного удаления.
        """
        stmt = delete(Bloodline).where(Bloodline.bloodline_id == bloodline_id)
        result = await self.db.execute(stmt)
        await self.db.commit() # commit здесь, так как это отдельная операция удаления
        return result.rowcount > 0 # Возвращаем True, если была удалена хотя бы одна строка