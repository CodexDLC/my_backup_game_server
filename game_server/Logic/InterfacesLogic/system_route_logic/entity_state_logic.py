from game_server.Logic.CRUD_LOGIC.CRUD.system.world.crud_state_entities import manage_entity_state_map



class EntityStateLogic:
    """Класс для управления состояниями и связями между entity_access_key ↔ access_code."""

    @staticmethod
    async def get_all_mappings(db_session):
        """Получить все связи entity_access_key ↔ access_code"""
        return await manage_entity_state_map("get", db_session=db_session)

    @staticmethod
    async def add_mapping(entity_access_key: str, access_code: int, db_session):
        """Добавить новую связь между entity_access_key и access_code"""
        return await manage_entity_state_map(
            "insert",
            entity_access_key=entity_access_key,
            state_data={"access_code": access_code},
            db_session=db_session
        )

    @staticmethod
    async def get_mapping(entity_access_key: str, db_session):
        """Получить список access_code для указанного entity_access_key"""
        return await manage_entity_state_map("get", entity_access_key=entity_access_key, db_session=db_session)

    @staticmethod
    async def delete_mapping(entity_access_key: str, access_code: int, db_session):
        """Удалить связь между entity_access_key и access_code"""
        return await manage_entity_state_map(
            "delete",
            entity_access_key=entity_access_key,
            state_data={"access_code": access_code},
            db_session=db_session
        )
