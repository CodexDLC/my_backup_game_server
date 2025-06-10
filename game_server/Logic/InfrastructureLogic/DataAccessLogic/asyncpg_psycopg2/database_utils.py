# database_utils.py
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging.logging_setup import logger




# Логгер
logger.basicConfig(
    level=logger.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


class DatabaseUtils:
    def __init__(self, db_name, db_user, db_password, db_host, db_port):
        self.db_name     = db_name
        self.db_user     = db_user
        self.db_password = db_password
        self.db_host     = db_host
        self.db_port     = db_port

    async def connect(self):
        """Устанавливает асинхронное соединение к БД."""
        try:
            async with get_db_session() as session:
                logger.info(f"Connected to {self.db_name}@{self.db_host}:{self.db_port}")
                return session
        except Exception as e:
            logger.error(f"Connect failed: {e}")
            raise

    async def execute_query(self, query: str, params: tuple = ()):
        """
        Выполняет INSERT/UPDATE/DELETE.
        :param query: SQL с $1, $2 …
        :param params: кортеж параметров
        """
        async with get_db_session() as session:
            try:
                result = await session.execute(query, *params) if params else await session.execute(query)
                logger.debug(f"Result: {result}")
                return result
            except Exception as e:
                logger.error(f"Query error: {e}")
                raise

    async def fetch_data(self, table_name: str, columns: list):
        """
        Выполняет SELECT и возвращает все строки.
        :return: список Record
        """
        async with get_db_session() as session:
            fields = ", ".join(columns)
            query = f"SELECT {fields} FROM {table_name}"
            try:
                result = await session.execute(query)
                rows = result.fetchall()
                logger.info(f"Fetched {len(rows)} rows from {table_name}")
                return rows
            except Exception as e:
                logger.error(f"Fetch error: {e}")
                raise

    async def fetch_row(self, query: str, *params):
        """
        Выполняет SELECT и возвращает первую строку или None.
        """
        async with get_db_session() as session:
            try:
                row = await session.fetchrow(query, *params)
                logger.debug(f"Row: {row}")
                return row
            except Exception as e:
                logger.error(f"FetchRow error: {e}")
                raise

    async def close_connection(self):
        """Закрывает соединение."""
        # Для асинхронных сессий закрытие сессии происходит автоматически при выходе из блока async with
        logger.info("Connection closed.")
