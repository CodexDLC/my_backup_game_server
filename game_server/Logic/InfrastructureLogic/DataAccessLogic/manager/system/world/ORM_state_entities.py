# game_server\Logic\ORM_LOGIC\managers\orm_entity_properties.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from game_server.database.models.models import EntityStateMap, StateEntity




class EntityStateMapManager:
    """Менеджер для работы с `entity_state_map` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_state(self, entity_access_key: str, state_data: dict):
        """Добавление состояния сущности."""
        state = EntityStateMap(entity_access_key=entity_access_key, **state_data)
        self.db_session.add(state)
        await self.db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['access_code']}` привязано к `{entity_access_key}`"}

    async def get_states(self, entity_access_key: str):
        """Получение состояний сущности."""
        query = select(EntityStateMap).where(EntityStateMap.entity_access_key == entity_access_key)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Состояния не найдены"}

    async def update_state(self, entity_access_key: str, state_data: dict):
        """Обновление состояния сущности."""
        query = select(EntityStateMap).where(EntityStateMap.entity_access_key == entity_access_key)
        result = await self.db_session.execute(query)
        state = result.scalar()

        if state:
            for key, value in state_data.items():
                setattr(state, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Состояние `{state_data['access_code']}` обновлено для `{entity_access_key}`"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_state(self, entity_access_key: str):
        """Удаление состояния сущности."""
        query = select(EntityStateMap).where(EntityStateMap.entity_access_key == entity_access_key)
        result = await self.db_session.execute(query)
        state = result.scalar()

        if state:
            await self.db_session.delete(state)
            await self.db_session.commit()
            return {"status": "success", "message": f"Состояние сущности `{entity_access_key}` удалено"}
        return {"status": "error", "message": "Запись не найдена"}




class StateEntitiesManager:
    """Менеджер для работы с `state_entities` через ORM."""

    @staticmethod
    async def get_all_states():
        """Получает список всех ролей (состояний)."""
        async for db_session in get_db_session():  # 🔥 Изменяем `async with` на `async for`
            query = select(StateEntity)
            result = await db_session.execute(query)
            states = result.scalars().all()
            return {"status": "success", "data": [state.__dict__ for state in states]}


    @staticmethod
    async def create_state(state_data: dict):
        """Добавляет новое состояние."""
        async with get_db_session() as db_session:  # ✅ Используем исправленный контекст
            state = StateEntity(**state_data)
            db_session.add(state)
            await db_session.commit()
            return {"status": "success", "message": f"Состояние `{state_data['code_name']}` добавлено"}


    @staticmethod
    async def get_state_by_access_code(access_code: int):
        """Получает данные состояния по `access_code`."""
        async with get_db_session() as db_session:  # ✅ Используем исправленный контекст
            query = select(StateEntity).where(StateEntity.access_code == access_code)
            result = await db_session.execute(query)
            state = result.scalar()
            return {"status": "success", "data": state.__dict__} if state else {"status": "error", "message": "Состояние не найдено"}


    @staticmethod
    async def update_state_status(access_code: int, is_active: bool):
        """Обновляет `is_active` статус состояния."""
        async with get_db_session() as db_session:  # ✅ Используем исправленный контекст
            query = select(StateEntity).where(StateEntity.access_code == access_code)
            result = await db_session.execute(query)
            state = result.scalar()

            if state:
                state.is_active = is_active
                await db_session.commit()
                return {"status": "success", "message": f"Статус `{state.code_name}` обновлён: {'активен' if is_active else 'выключен'}"}
            return {"status": "error", "message": "Состояние не найдено"}


