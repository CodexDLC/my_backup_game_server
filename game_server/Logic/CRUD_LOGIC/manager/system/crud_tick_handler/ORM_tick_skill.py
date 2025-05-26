from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import SkillAbilityUnlocks, SkillUnlocks

class SkillUnlocksManager:
    """Менеджер для работы с `skill_unlocks` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_unlock(self, skill_key: str, rank: int, unlock_data: dict):
        """Добавление нового разблокируемого ранга навыка."""
        unlock = SkillUnlocks(skill_key=skill_key, rank=rank, **unlock_data)
        self.db_session.add(unlock)
        await self.db_session.commit()
        return {"status": "success", "message": f"Ранг `{rank}` для `{skill_key}` добавлен"}

    async def get_unlock(self, skill_key: str = None, rank: int = None):
        """Получение разблокированных рангов навыка."""
        query = select(SkillUnlocks)
        
        if skill_key:
            query = query.where(SkillUnlocks.skill_key == skill_key)
        if rank:
            query = query.where(SkillUnlocks.rank == rank)

        result = await self.db_session.execute(query)
        rows = result.scalars().all()

        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Ранги не найдены"}

    async def update_unlock(self, skill_key: str, rank: int, unlock_data: dict):
        """Обновление разблокируемого ранга навыка."""
        query = select(SkillUnlocks).where(SkillUnlocks.skill_key == skill_key, SkillUnlocks.rank == rank)
        result = await self.db_session.execute(query)
        unlock = result.scalar()

        if unlock:
            for key, value in unlock_data.items():
                setattr(unlock, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Ранг `{rank}` для `{skill_key}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_unlock(self, skill_key: str, rank: int):
        """Удаление разблокируемого ранга навыка."""
        query = select(SkillUnlocks).where(SkillUnlocks.skill_key == skill_key, SkillUnlocks.rank == rank)
        result = await self.db_session.execute(query)
        unlock = result.scalar()

        if unlock:
            await self.db_session.delete(unlock)
            await self.db_session.commit()
            return {"status": "success", "message": f"Ранг `{rank}` для `{skill_key}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}


class SkillAbilityUnlocksManager:
    """Менеджер для работы с `skill_ability_unlocks` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_unlock(self, skill_key: str, level: int, ability_key: str):
        """Добавление новой записи в таблицу `skill_ability_unlocks`."""
        unlock = SkillAbilityUnlocks(skill_key=skill_key, level=level, ability_key=ability_key)
        self.db_session.add(unlock)
        await self.db_session.commit()
        return {"status": "success", "message": f"Способность `{ability_key}` для `{skill_key}` (уровень {level}) добавлена"}

    async def get_unlocks(self, skill_key: str = None, level: int = None, ability_key: str = None):
        """Получение записей по заданным параметрам."""
        query = select(SkillAbilityUnlocks)

        if skill_key:
            query = query.where(SkillAbilityUnlocks.skill_key == skill_key)
        if level:
            query = query.where(SkillAbilityUnlocks.level == level)
        if ability_key:
            query = query.where(SkillAbilityUnlocks.ability_key == ability_key)

        result = await self.db_session.execute(query)
        rows = result.scalars().all()

        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Способности не найдены"}

    async def update_unlock(self, skill_key: str, level: int, ability_key: str, update_data: dict):
        """Обновление записи в таблице `skill_ability_unlocks`."""
        query = select(SkillAbilityUnlocks).where(
            SkillAbilityUnlocks.skill_key == skill_key,
            SkillAbilityUnlocks.level == level,
            SkillAbilityUnlocks.ability_key == ability_key
        )
        result = await self.db_session.execute(query)
        unlock = result.scalar()

        if unlock:
            for key, value in update_data.items():
                setattr(unlock, key, value)
            
            await self.db_session.commit()
            return {"status": "success", "message": f"Способность `{ability_key}` обновлена для `{skill_key}` (уровень {level})"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_unlock(self, skill_key: str, level: int, ability_key: str):
        """Удаление записи из `skill_ability_unlocks`."""
        query = select(SkillAbilityUnlocks).where(
            SkillAbilityUnlocks.skill_key == skill_key,
            SkillAbilityUnlocks.level == level,
            SkillAbilityUnlocks.ability_key == ability_key
        )
        result = await self.db_session.execute(query)
        unlock = result.scalar()

        if unlock:
            await self.db_session.delete(unlock)
            await self.db_session.commit()
            return {"status": "success", "message": f"Способность `{ability_key}` удалена из `{skill_key}` (уровень {level})"}
        return {"status": "error", "message": "Запись не найдена"}