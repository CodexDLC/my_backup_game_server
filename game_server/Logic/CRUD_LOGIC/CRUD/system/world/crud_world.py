from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text



class ManageWorld:
    @staticmethod
    async def manage_worlds(action: str, world_id: str = None, world_data: dict = None, db_session: AsyncSession = None):
        """
        Универсальная функция для работы с таблицей `worlds` (INSERT, SELECT, UPDATE, DELETE).

        :param action: Действие ("insert", "get", "update", "delete").
        :param world_id: ID мира (нужно для "get", "update", "delete").
        :param world_data: Данные для вставки/обновления (например, {"name": "Fantasy World", "is_static": True}).
        :param db_session: Асинхронная сессия базы данных.
        :return: Результат операции.
        """

        if action == "insert" and world_data:
            query = text("""
                INSERT INTO worlds (id, name, is_static, created_at)
                VALUES (gen_random_uuid(), :name, :is_static, NOW())
            """)
            await db_session.execute(query, world_data)
            await db_session.commit()
            return {"status": "success", "message": f"Мир `{world_data['name']}` создан"}

        elif action == "get" and world_id:
            query = text("SELECT * FROM worlds WHERE id = :world_id")
            result = await db_session.execute(query, {"world_id": world_id})
            row = result.fetchone()
            return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Мир не найден"}

        elif action == "update" and world_id and world_data:
            updates = ", ".join(f"{key} = :{key}" for key in world_data.keys())
            query = text(f"""
                UPDATE worlds SET {updates}, created_at = NOW()
                WHERE id = :world_id
            """)
            await db_session.execute(query, {"world_id": world_id, **world_data})
            await db_session.commit()
            return {"status": "success", "message": f"Мир `{world_id}` обновлён"}

        elif action == "delete" and world_id:
            query = text("DELETE FROM worlds WHERE id = :world_id")
            await db_session.execute(query, {"world_id": world_id})
            await db_session.commit()
            return {"status": "success", "message": f"Мир `{world_id}` удалён"}

        return {"status": "error", "message": "Неверные параметры запроса"}

    @staticmethod
    async def manage_regions(action: str, region_id: str = None, region_data: dict = None, db_session: AsyncSession = None):
        """
        Универсальная функция для работы с таблицей `regions` (INSERT, SELECT, UPDATE, DELETE).

        :param action: Действие ("insert", "get", "update", "delete").
        :param region_id: ID региона (нужно для "get", "update", "delete").
        :param region_data: Данные для вставки/обновления (например, {"world_id": "uuid", "name": "Mystic Lands"}).
        :param db_session: Асинхронная сессия базы данных.
        :return: Результат операции.
        """

        if action == "insert" and region_data:
            query = text("""
                INSERT INTO regions (id, world_id, access_key, name, description)
                VALUES (gen_random_uuid(), :world_id, :access_key, :name, :description)
            """)
            await db_session.execute(query, region_data)
            await db_session.commit()
            return {"status": "success", "message": f"Регион `{region_data['name']}` создан"}

        elif action == "get" and region_id:
            query = text("SELECT * FROM regions WHERE id = :region_id")
            result = await db_session.execute(query, {"region_id": region_id})
            row = result.fetchone()
            return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Регион не найден"}

        elif action == "update" and region_id and region_data:
            updates = ", ".join(f"{key} = :{key}" for key in region_data.keys())
            query = text(f"""
                UPDATE regions SET {updates}
                WHERE id = :region_id
            """)
            await db_session.execute(query, {"region_id": region_id, **region_data})
            await db_session.commit()
            return {"status": "success", "message": f"Регион `{region_id}` обновлён"}

        elif action == "delete" and region_id:
            query = text("DELETE FROM regions WHERE id = :region_id")
            await db_session.execute(query, {"region_id": region_id})
            await db_session.commit()
            return {"status": "success", "message": f"Регион `{region_id}` удалён"}

        return {"status": "error", "message": "Неверные параметры запроса"}

    @staticmethod
    async def manage_subregions(action: str, subregion_id: str = None, subregion_data: dict = None, db_session: AsyncSession = None):
        """
        Универсальная функция для работы с таблицей `subregions` (INSERT, SELECT, UPDATE, DELETE).

        :param action: Действие ("insert", "get", "update", "delete").
        :param subregion_id: ID субрегиона (нужно для "get", "update", "delete").
        :param subregion_data: Данные для вставки/обновления (например, {"region_id": "uuid", "name": "Ancient Ruins"}).
        :param db_session: Асинхронная сессия базы данных.
        :return: Результат операции.
        """

        if action == "insert" and subregion_data:
            query = text("""
                INSERT INTO subregions (id, region_id, access_key, name, description, is_peaceful)
                VALUES (gen_random_uuid(), :region_id, :access_key, :name, :description, :is_peaceful)
            """)
            await db_session.execute(query, subregion_data)
            await db_session.commit()
            return {"status": "success", "message": f"Субрегион `{subregion_data['name']}` создан"}

        elif action == "get" and subregion_id:
            query = text("SELECT * FROM subregions WHERE id = :subregion_id")
            result = await db_session.execute(query, {"subregion_id": subregion_id})
            row = result.fetchone()
            return {"status": "found", "data": dict(row)} if row else {"status": "error", "message": "Субрегион не найден"}

        elif action == "update" and subregion_id and subregion_data:
            updates = ", ".join(f"{key} = :{key}" for key in subregion_data.keys())
            query = text(f"""
                UPDATE subregions SET {updates}
                WHERE id = :subregion_id
            """)
            await db_session.execute(query, {"subregion_id": subregion_id, **subregion_data})
            await db_session.commit()
            return {"status": "success", "message": f"Субрегион `{subregion_id}` обновлён"}

        elif action == "delete" and subregion_id:
            query = text("DELETE FROM subregions WHERE id = :subregion_id")
            await db_session.execute(query, {"subregion_id": subregion_id})
            await db_session.commit()
            return {"status": "success", "message": f"Субрегион `{subregion_id}` удалён"}

        return {"status": "error", "message": "Неверные параметры запроса"}
