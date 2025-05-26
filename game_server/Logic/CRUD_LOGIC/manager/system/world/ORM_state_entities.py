# game_server\Logic\ORM_LOGIC\managers\orm_entity_properties.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import EntityProperties, EntityStateMap, StateEntities

class EntityPropertiesManager:
    """Менеджер для работы с `entity_properties` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_property(self, entity_id: str, property_data: dict):
        """Добавление нового параметра сущности."""
        property_record = EntityProperties(entity_id=entity_id, **property_data)
        self.db_session.add(property_record)
        await self.db_session.commit()
        return {"status": "success", "message": f"Параметр `{property_data['key']}` добавлен для сущности `{entity_id}`"}

    async def get_properties(self, entity_id: str):
        """Получение параметров сущности."""
        query = select(EntityProperties).where(EntityProperties.entity_id == entity_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()
        return {"status": "found", "data": [row.__dict__ for row in rows]} if rows else {"status": "error", "message": "Параметры не найдены"}

    async def update_property(self, entity_id: str, property_data: dict):
        """Обновление параметра сущности."""
        query = select(EntityProperties).where(EntityProperties.entity_id == entity_id, EntityProperties.key == property_data["key"])
        result = await self.db_session.execute(query)
        property_record = result.scalar()

        if property_record:
            property_record.value = property_data["value"]
            await self.db_session.commit()
            return {"status": "success", "message": f"Параметр `{property_data['key']}` обновлён для сущности `{entity_id}`"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_property(self, entity_id: str):
        """Удаление параметров сущности."""
        query = select(EntityProperties).where(EntityProperties.entity_id == entity_id)
        result = await self.db_session.execute(query)
        rows = result.scalars().all()

        if rows:
            for row in rows:
                await self.db_session.delete(row)

            await self.db_session.commit()
            return {"status": "success", "message": f"Параметры сущности `{entity_id}` удалены"}
        return {"status": "error", "message": "Запись не найдена"}


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

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_state(self, access_code: int, state_data: dict):
        """Добавление нового состояния."""
        state = StateEntities(access_code=access_code, **state_data)
        self.db_session.add(state)
        await self.db_session.commit()
        return {"status": "success", "message": f"Состояние `{state_data['code_name']}` добавлено"}

    async def get_state(self, access_code: int):
        """Получение состояния по access_code."""
        query = select(StateEntities).where(StateEntities.access_code == access_code)
        result = await self.db_session.execute(query)
        state = result.scalar()
        return {"status": "found", "data": state.__dict__} if state else {"status": "error", "message": "Состояние не найдено"}

    async def update_state(self, access_code: int, state_data: dict):
        """Обновление состояния."""
        query = select(StateEntities).where(StateEntities.access_code == access_code)
        result = await self.db_session.execute(query)
        state = result.scalar()

        if state:
            for key, value in state_data.items():
                setattr(state, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Состояние `{state_data['code_name']}` обновлено"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_state(self, access_code: int):
        """Удаление состояния."""
        query = select(StateEntities).where(StateEntities.access_code == access_code)
        result = await self.db_session.execute(query)
        state = result.scalar()

        if state:
            await self.db_session.delete(state)
            await self.db_session.commit()
            return {"status": "success", "message": f"Состояние `{access_code}` удалено"}
        return {"status": "error", "message": "Запись не найдена"}
