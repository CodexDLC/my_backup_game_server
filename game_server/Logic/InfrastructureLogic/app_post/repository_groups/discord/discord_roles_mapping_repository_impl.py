# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/discord/discord_roles_mapping_repository_impl.py

import datetime
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError # Исправлено: из sqlalchemy.exc

# Импортируем вашу модель StateEntityDiscord
from game_server.database.models.models import StateEntityDiscord

# Импортируем интерфейс репозитория # <--- ИСПРАВЛЕНИЕ: ДОБАВЛЕН ИМПОРТ ИНТЕРФЕЙСА
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordRolesMappingRepository

# Импортируем настроенный глобальный логгер сервера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger


class DiscordRolesMappingRepositoryImpl(IDiscordRolesMappingRepository): # <--- ИЗМЕНЕНО: Наследование и имя класса
    """
    Репозиторий для работы с `state_entities_discord` через ORM.
    Взаимодействует напрямую с базой данных через SQLAlchemy ORM.
    Все операции создания/обновления используют UPSERT-логику.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        logger.debug("Инициализация DiscordRolesMappingRepositoryImpl с переданной сессией БД.")

    # --- 1. Одиночный UPSERT (создание или обновление одной записи о роли) ---
    async def create_or_update_single_role(self, role_data: Dict[str, Any]) -> Optional[StateEntityDiscord]:
        """
        Создает или обновляет одну запись о роли Discord.
        Использует UPSERT-логику (ON CONFLICT DO UPDATE) по композитному PK (guild_id, role_id).
        Возвращает созданный/обновленный ORM-объект.
        """
        if not isinstance(role_data, dict):
            logger.warning("Некорректные данные для одиночной вставки роли: ожидался словарь.")
            raise ValueError("Некорректные данные, ожидался словарь.")

        role_data['updated_at'] = datetime.datetime.now(datetime.timezone.utc)

        try:
            stmt = insert(StateEntityDiscord).values(role_data)

            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=['guild_id', 'role_id'],
                set_={
                    'access_code': stmt.excluded.access_code,
                    'role_name': stmt.excluded.role_name, 
                    'permissions': stmt.excluded.permissions, 
                    'updated_at': stmt.excluded.updated_at
                }
            ).returning(StateEntityDiscord)

            result = await self.db_session.execute(on_conflict_stmt)
            await self.db_session.flush()

            entity = result.scalar_one_or_none()
            if not entity:
                raise RuntimeError("Ошибка: UPSERT не вернул объект.")

            logger.info(f"✅ Успешно добавлен/обновлен роль '{entity.role_name}' (Guild ID: {entity.guild_id}, Role ID: {entity.role_id}) в БД.")
            return entity
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка целостности при одиночном сохранении/обновлении роли: {e.orig}", exc_info=True)
            raise ValueError(f"Ошибка целостности при сохранении роли: {e.orig}")
        except Exception as e:
            await self.db_session.rollback() 
            logger.error(f"❌ Непредвиденная ошибка одиночного сохранения/обновления роли: {e}", exc_info=True)
            raise


    # --- 2. Массовый/Батчевый UPSERT (создание или обновление нескольких записей о ролях) ---
    async def create_or_update_roles_batch(self, roles_data: List[Dict[str, Any]]) -> int:
        """
        Массовое добавление/обновление записей о ролях Discord (Upsert).
        Если запись с таким (guild_id, role_id) уже существует, она будет обновлена.
        Принимает список словарей, где каждый словарь соответствует полям StateEntityDiscord.
        Возвращает количество обработанных (вставленных/обновленных) записей.
        """
        if not roles_data:
            logger.warning("Нет данных для массовой вставки/обновления ролей.")
            return 0

        processed_roles_data = []
        for role_data in roles_data:
            if not isinstance(role_data, dict):
                logger.warning(f"Пропущена некорректная запись для массовой вставки роли: {role_data}")
                continue
            role_data_copy = role_data.copy()
            role_data_copy['updated_at'] = datetime.datetime.now(datetime.timezone.utc)
            if 'access_code' in role_data_copy and role_data_copy['access_code'] is not None and not isinstance(role_data_copy['access_code'], str):
                 role_data_copy['access_code'] = str(role_data_copy['access_code'])
            processed_roles_data.append(role_data_copy)

        if not processed_roles_data:
            logger.warning("После обработки не осталось корректных данных для массовой вставки/обновления ролей.")
            return 0

        try:
            stmt = insert(StateEntityDiscord).values(processed_roles_data)

            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=['guild_id', 'role_id'],
                set_={
                    'access_code': stmt.excluded.access_code,
                    'role_name': stmt.excluded.role_name, 
                    'permissions': stmt.excluded.permissions, 
                    'updated_at': stmt.excluded.updated_at
                }
            )

            result = await self.db_session.execute(on_conflict_stmt)
            await self.db_session.flush()

            processed_count = result.rowcount
            logger.info(f"✅ Успешно добавлено/обновлено {processed_count} ролей в БД.")
            return processed_count
        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка целостности при массовом сохранении/обновлении ролей в БД: {e.orig}", exc_info=True)
            raise ValueError(f"Ошибка целостности при массовом сохранении: {e.orig}")
        except Exception as e:
            await self.db_session.rollback() 
            logger.error(f"❌ Непредвиденная ошибка массового сохранения/обновления ролей в БД: {e}", exc_info=True)
            raise


    # --- 3. Получение одной записи о роли по ПК ---
    async def get_role_by_pk(self, guild_id: int, role_id: int) -> Optional[StateEntityDiscord]:
        """Получение одной записи о роли по полному первичному ключу (guild_id, role_id)."""
        logger.debug(f"Запрос роли Discord по PK: (guild_id={guild_id}, role_id={role_id})")
        stmt = select(StateEntityDiscord).where(
            StateEntityDiscord.guild_id == guild_id,
            StateEntityDiscord.role_id == role_id
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()


    # --- 4. Получение всех записей о ролях для гильдии ---
    async def get_all_roles_for_guild(self, guild_id: int) -> List[StateEntityDiscord]:
        """Получение ВСЕХ записей о ролях для конкретного guild_id."""
        logger.debug(f"Запрос всех ролей Discord для гильдии {guild_id}.")
        stmt = select(StateEntityDiscord).where(StateEntityDiscord.guild_id == guild_id)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())


    # --- 5. Удаление одной записи о роли по ПК ---
    async def delete_role_by_pk(self, guild_id: int, role_id: int) -> bool:
        """
        Удаление одной записи о роли по полному первичному ключу (guild_id, role_id).
        Возвращает True, если запись была удалена, False в противном случае.
        """
        logger.info(f"Удаление роли Discord по PK: (guild_id={guild_id}, role_id={role_id})")
        try:
            stmt = delete(StateEntityDiscord).where(
                StateEntityDiscord.guild_id == guild_id,
                StateEntityDiscord.role_id == role_id
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.flush()

            if result.rowcount > 0:
                logger.info(f"✅ Роль Discord (guild_id={guild_id}, role_id={role_id}) успешно помечена для удаления в БД.")
                return True
            else:
                logger.warning(f"Роль Discord с PK (guild_id={guild_id}, role_id={role_id}) не найдена для удаления.")
                return False
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка удаления роли Discord по ПК: {e}", exc_info=True)
            raise


    # --- Дополнительный метод: Массовое удаление по Discord role_id ---
    async def delete_roles_by_discord_ids(self, discord_role_ids: List[int]) -> int:
        """
        Массовое удаление записей из таблицы `state_entities_discord` по `role_id`.
        Удаляет все записи, у которых `role_id` входит в переданный список.
        Возвращает количество удаленных записей.
        """
        if not discord_role_ids:
            logger.info("Нет ID ролей Discord для массового удаления из БД.")
            return 0

        try:
            stmt = delete(StateEntityDiscord).where(StateEntityDiscord.role_id.in_(discord_role_ids))

            result = await self.db_session.execute(stmt)
            await self.db_session.flush()

            deleted_rows = result.rowcount
            logger.info(f"✅ Успешно удалено {deleted_rows} записей ролей из БД.")
            return deleted_rows
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"❌ Ошибка при массовом удалении ролей из БД по Discord ID: {e}", exc_info=True)
            raise