
# game_server\Logic\ORM_LOGIC\managers\orm_connection_types.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from game_server.database.models.models import ConnectionTypes, Connections

class ConnectionTypesManager:
    """Менеджер для работы с `connection_types` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_connection_type(self, type_id: str, type_data: dict):
        """Добавление нового типа связи."""
        connection_type = ConnectionTypes(id=type_id, **type_data)
        self.db_session.add(connection_type)
        await self.db_session.commit()
        return {"status": "success", "message": f"Тип `{type_data['name']}` добавлен"}

    async def get_connection_type(self, type_id: str):
        """Получение типа связи по ID."""
        query = select(ConnectionTypes).where(ConnectionTypes.id == type_id)
        result = await self.db_session.execute(query)
        connection_type = result.scalar()
        return {"status": "found", "data": connection_type.__dict__} if connection_type else {"status": "error", "message": "Тип связи не найден"}

    async def update_connection_type(self, type_id: str, type_data: dict):
        """Обновление типа связи."""
        query = select(ConnectionTypes).where(ConnectionTypes.id == type_id)
        result = await self.db_session.execute(query)
        connection_type = result.scalar()

        if connection_type:
            for key, value in type_data.items():
                setattr(connection_type, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Тип `{type_id}` обновлён"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_connection_type(self, type_id: str):
        """Удаление типа связи."""
        query = select(ConnectionTypes).where(ConnectionTypes.id == type_id)
        result = await self.db_session.execute(query)
        connection_type = result.scalar()

        if connection_type:
            await self.db_session.delete(connection_type)
            await self.db_session.commit()
            return {"status": "success", "message": f"Тип `{type_id}` удалён"}
        return {"status": "error", "message": "Запись не найдена"}
    





class ConnectionsManager:
    """Менеджер для работы с `connections` через ORM."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_connection(self, connection_id: str, connection_data: dict):
        """Добавление новой связи."""
        connection = Connections(id=connection_id, **connection_data)
        self.db_session.add(connection)
        await self.db_session.commit()
        return {"status": "success", "message": f"Связь `{connection_data['from_type']} → {connection_data['to_type']}` добавлена"}

    async def get_connection(self, connection_id: str):
        """Получение связи по ID."""
        query = select(Connections).where(Connections.id == connection_id)
        result = await self.db_session.execute(query)
        connection = result.scalar()
        return {"status": "found", "data": connection.__dict__} if connection else {"status": "error", "message": "Связь не найдена"}

    async def update_connection(self, connection_id: str, connection_data: dict):
        """Обновление связи."""
        query = select(Connections).where(Connections.id == connection_id)
        result = await self.db_session.execute(query)
        connection = result.scalar()

        if connection:
            for key, value in connection_data.items():
                setattr(connection, key, value)

            await self.db_session.commit()
            return {"status": "success", "message": f"Связь `{connection_id}` обновлена"}
        return {"status": "error", "message": "Запись не найдена"}

    async def delete_connection(self, connection_id: str):
        """Удаление связи."""
        query = select(Connections).where(Connections.id == connection_id)
        result = await self.db_session.execute(query)
        connection = result.scalar()

        if connection:
            await self.db_session.delete(connection)
            await self.db_session.commit()
            return {"status": "success", "message": f"Связь `{connection_id}` удалена"}
        return {"status": "error", "message": "Запись не найдена"}
