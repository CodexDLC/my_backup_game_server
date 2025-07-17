# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/npc/monster/elite_monster_repository_impl.py

import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession # Принимает активную сессию
from sqlalchemy import select, update, delete
from sqlalchemy.future import select as fselect
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Импорт вашей модели EliteMonster
from game_server.database.models.models import EliteMonster

# Импорт интерфейса репозитория
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.npc.monster.interfaces_monster import IEliteMonsterRepository


# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger


class EliteMonsterRepositoryImpl(IEliteMonsterRepository):
    """
    Репозиторий для выполнения CRUD-операций с моделью EliteMonster.
    Теперь работает с переданной активной сессией и не управляет транзакциями.
    """
    # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем активную сессию
    def __init__(self, db_session: AsyncSession):
        self._session = db_session # <--- СОХРАНЯЕМ АКТИВНУЮ СЕССИЮ
        logger.info(f"✅ {self.__class__.__name__} инициализирован с активной сессией.")

    async def create_monster(self, data: Dict[str, Any]) -> EliteMonster: # Переименовано для соответствия интерфейсу
        """
        Создает новую запись элитного монстра в рамках переданной сессии.
        """
        new_monster = EliteMonster(**data)
        self._session.add(new_monster)
        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Элитный монстр (ID: {new_monster.monster_instance_id if hasattr(new_monster, 'monster_instance_id') else 'N/A'}) добавлен в сессию.")
        return new_monster

    async def get_monster_by_id(self, monster_instance_id: int) -> Optional[EliteMonster]: # Переименовано для соответствия интерфейсу
        """
        Получает элитного монстра по его ID экземпляра в рамках переданной сессии.
        """
        result = await self._session.get(EliteMonster, monster_instance_id)
        return result

    async def get_all_monsters(self, is_active: Optional[bool] = None) -> List[EliteMonster]: # Переименовано для соответствия интерфейсу
        """
        Получает всех элитных монстров, опционально фильтруя по статусу активности, в рамках переданной сессии.
        """
        stmt = fselect(EliteMonster)
        if is_active is not None:
            stmt = stmt.where(EliteMonster.is_active == is_active)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_monster_by_name(self, display_name: str) -> Optional[EliteMonster]:
        """
        Получает элитного монстра по его отображаемому имени в рамках переданной сессии.
        """
        stmt = fselect(EliteMonster).where(EliteMonster.display_name == display_name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_monster(self, monster_instance_id: int, updates: Dict[str, Any]) -> Optional[EliteMonster]: # Переименовано для соответствия интерфейсу
        """
        Обновляет существующего элитного монстра по его ID экземпляра в рамках переданной сессии.
        """
        stmt = update(EliteMonster).where(EliteMonster.monster_instance_id == monster_instance_id).values(**updates).returning(EliteMonster)
        result = await self._session.execute(stmt)
        updated_monster = result.scalars().first()
        if updated_monster:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Элитный монстр (ID: {monster_instance_id}) обновлен в сессии.")
        else:
            logger.warning(f"Элитный монстр с ID {monster_instance_id} не найден для обновления.")
        return updated_monster

    async def delete_monster(self, monster_instance_id: int) -> bool: # Переименовано для соответствия интерфейсу
        """
        Удаляет элитного монстра по его ID экземпляра в рамках переданной сессии.
        """
        stmt = delete(EliteMonster).where(EliteMonster.monster_instance_id == monster_instance_id)
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            await self._session.flush() # flush, но НЕ commit
            logger.info(f"Элитный монстр (ID: {monster_instance_id}) помечен для удаления в сессии.")
            return True
        else:
            logger.warning(f"Элитный монстр с ID {monster_instance_id} не найден для удаления.")
            return False

    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Массово создает или обновляет записи элитных монстров в рамках переданной сессии.
        """
        if not data_list:
            logger.info("Пустой список данных для EliteMonster upsert_many. Ничего не сделано.")
            return 0, 0

        # Определение полей для обновления при конфликте
        # Исключаем 'monster_instance_id', так как это PK с autoincrement
        updatable_fields = [
            "monster_template_id", "display_name", "current_location",
            "last_player_killed_id", "killed_players_count", "current_status",
            "killed_by_info_json", "unique_modifiers_json", "is_active",
            "spawn_priority", "last_seen_at" # created_at не обновляем
        ]

        # Создаем словарь для set_ на основе excluded полей
        set_clause = {field: getattr(pg_insert(EliteMonster).excluded, field) for field in updatable_fields}

        insert_stmt = pg_insert(EliteMonster).values(data_list)
        on_conflict_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[EliteMonster.monster_instance_id], # Используем PK для определения конфликта
            set_=set_clause
        ).returning(EliteMonster.monster_instance_id) # Возвращаем PK, чтобы посчитать сколько было затронуто

        result = await self._session.execute(on_conflict_stmt)

        # SQLAlchemy возвращает rowcount, который для upsert может быть не совсем точным по insert/update.
        # Однако, для do_update он обычно показывает количество обновленных/вставленных строк.
        total_affected = result.rowcount # Это общее количество затронутых строк

        # Более точный подсчет inserted/updated требует либо проверки каждой строки, либо специфичных методов в базе.
        # Для простоты, здесь мы не можем легко различить insert и update без дополнительных запросов
        # или возвращения полного объекта и сравнения.
        # Пока возвращаем (затронуто, 0), или можно попробовать приблизительно.
        inserted_count = total_affected # Простая аппроксимация
        updated_count = 0 # Простая аппроксимация

        await self._session.flush() # flush, но НЕ commit
        logger.info(f"Успешно массово добавлено/обновлено {total_affected} элитных монстров в сессии.")
        return inserted_count, updated_count
