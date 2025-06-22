# Discord_API/core/services/admin/role_management_service.py

import logging
from typing import Dict, Any, List, Optional
import discord
from discord import Guild, Role, Forbidden, HTTPException, NotFound, utils
import datetime

# Импорт клиента для взаимодействия с нашим БЭКЕНДОМ (FastAPI)
from Discord_API.core.api_route_function.spec_route.state_entities_discord_api import StateEntitiesDiscordAPIClient


# Импорт базовых операций Discord
from Discord_API.core.api_route_function.system.system_mapping_api import SystemMappingAPIClient
from Discord_API.core.services.admin.base_discord_operations import BaseDiscordOperations
# <--- УДАЛЕНО: Импорт from Discord_API.core.assets.data.roles_config import ROLES_CONFIG

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)


class RoleManagementService:
    """
    Сервисный слой для управления ролями Discord.
    Отвечает за:
    1. Получение ожидаемых ролей из базы данных на бэкенде (State Entities).
    2. Создание/обновление/удаление ролей в Discord.
    3. Синхронизацию данных о ролях (с Discord ID) с бэкендом (таблица StateEntityDiscord).
    """
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.base_ops = BaseDiscordOperations(bot)
        self.state_entities_api_client = SystemMappingAPIClient() # Клиент для получения State Entities из БД бэкенда
        self.roles_mapping_api_client = StateEntitiesDiscordAPIClient() # Клиент для StateEntityDiscord (привязки ролей)
        # <--- УДАЛЕНО: self.roles_config = ROLES_CONFIG

    async def sync_discord_roles(self, guild_id: int) -> Dict[str, Any]:
        """
        Синхронизирует Discord роли для указанной гильдии на основе `state_entities` из БД бэкенда.
        Создает отсутствующие роли, обновляет существующие, и сохраняет привязки в БД.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")

        logger.info(f"Начало синхронизации Discord ролей для гильдии {guild_id} ('{guild.name}').")

        created_count = 0
        updated_count = 0
        errors = []
        roles_to_sync_with_backend: List[Dict[str, Any]] = [] # Данные для таблицы StateEntityDiscord

        # 1. Получаем "ожидаемые" роли (access_level ИЛИ status_flag) из БД бэкенда
        response_from_backend = await self.state_entities_api_client.get_all_state_entities()
        
        # --- ИСПРАВЛЕНИЕ 2.1: Проверка на success: True в ответе бэкенда ---
        if not response_from_backend.get("success"):
            error_msg = response_from_backend.get("error", {}).get("message", "Неизвестная ошибка")
            logger.error(f"Не удалось получить State Entities с бэкенда: {error_msg}")
            raise RuntimeError(f"Не удалось получить ожидаемые роли с бэкенда: {error_msg}")
        
        expected_state_entities: List[Dict[str, Any]] = response_from_backend.get("data", [])
        
        # --- ИСПРАВЛЕНИЕ 1.1: Фильтруем только сущности, которые должны стать ролями ---
        # Теперь включаем и 'access_level', и 'status_flag'
        roles_for_processing = [
            item for item in expected_state_entities
            if item.get("ui_type") in ["access_level", "status_flag"] # Включаем оба типа
        ]

        if not roles_for_processing:
            logger.warning("Не найдено сущностей State Entities типа 'access_level' или 'status_flag' на бэкенде для синхронизации ролей.")
            return {"status": "success", "message": "Не найдено ролей для синхронизации."}


        # 2. Получаем текущие роли Discord из Guild API
        current_discord_roles = {role.name: role for role in guild.roles}

        # 3. Обработка создания/обновления ролей в Discord
        for expected_role_data in roles_for_processing: # Используем полный список ролей
            access_code = expected_role_data['access_code']
            discord_role_name = expected_role_data['description'] # description в StateEntityAPIResponse
            
            existing_discord_role = current_discord_roles.get(discord_role_name)

            try:
                role_obj: Optional[Role] = None
                if existing_discord_role:
                    role_obj = existing_discord_role
                    logger.info(f"Роль '{discord_role_name}' уже существует в Discord. Используем существующую.")
                    updated_count += 1
                else:
                    role_obj = await guild.create_role(name=discord_role_name)
                    logger.info(f"Создана роль в Discord: '{discord_role_name}' (ID: {role_obj.id}).")
                    created_count += 1
                
                if role_obj:
                    roles_to_sync_with_backend.append({
                        "guild_id": guild_id,
                        "role_id": role_obj.id,
                        "access_code": access_code,
                        "role_name": role_obj.name,
                        "permissions": expected_role_data.get('permissions')
                    })

            except Forbidden as e:
                logger.error(f"Бот не имеет прав для создания/обновления роли '{discord_role_name}': {e}", exc_info=True)
                errors.append({"role_name": discord_role_name, "error": f"Нет прав: {e}"})
            except HTTPException as e:
                logger.error(f"Ошибка Discord API при создании/обновлении роли '{discord_role_name}': {e}", exc_info=True)
                errors.append({"role_name": discord_role_name, "error": f"Ошибка Discord API: {e.status} {e.message}"})
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при обработке роли '{discord_role_name}': {e}", exc_info=True)
                errors.append({"role_name": discord_role_name, "error": f"Непредвиденная ошибка: {e}"})

        # 4. Отправка данных на бэкенд для массового UPSERT'а (таблица StateEntityDiscord)
        if roles_to_sync_with_backend:
            logger.info(f"Отправка {len(roles_to_sync_with_backend)} ролей на бэкенд для синхронизации...")
            try:
                sync_response = await self.roles_mapping_api_client.create_or_update_roles_batch(roles_to_sync_with_backend)
                
                # --- ИСПРАВЛЕНИЕ 2.2: Корректная проверка success-статуса ответа бэкенда ---
                if sync_response.get("success") is True: # Проверяем top-level "success" ключ
                    logger.info(f"Синхронизация ролей с бэкендом завершена: {sync_response.get('message')}")
                    # Дополнительно можно проверить status внутри data, если это необходимо
                    # if sync_response.get("data", {}).get("status") == "success":
                    #     logger.info("Детальный статус синхронизации в data: success")
                else:
                    logger.error(f"Бэкенд вернул ошибку при синхронизации ролей: {sync_response.get('message')}")
                    errors.append({"backend_sync": "Ошибка", "message": sync_response.get('message')})
            except (ConnectionError, ValueError, RuntimeError) as e:
                logger.error(f"Ошибка при синхронизации ролей с бэкендом: {e}", exc_info=True)
                errors.append({"backend_sync": "Ошибка", "message": str(e)})
        else:
            logger.info("Нет ролей для отправки на бэкенд для синхронизации.")
        
        return {
            "status": "success" if not errors else "partial_success",
            "message": "Синхронизация ролей завершена." if not errors else "Синхронизация ролей завершена с ошибками.",
            "details": {
                "created_discord_roles": created_count,
                "updated_discord_roles": updated_count,
                "errors": errors,
                "synced_to_backend_count": len(roles_to_sync_with_backend)
            }
        }

    async def delete_discord_roles_batch(self, guild_id: int, role_ids: List[int]) -> Dict[str, Any]:
        """
        Удаляет список ролей из Discord и соответствующие записи из БД.
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден или недоступен.")
        
        logger.info(f"Начало массового удаления Discord ролей для гильдии {guild_id}: {role_ids}.")
        
        deleted_from_discord_count = 0
        deleted_from_backend_count = 0
        errors = []

        for role_id in role_ids:
            try:
                role_obj = guild.get_role(role_id)
                if role_obj:
                    await role_obj.delete(reason="Удаление роли по команде бота.")
                    logger.info(f"Роль '{role_obj.name}' (ID: {role_obj.id}) успешно удалена из Discord.")
                    deleted_from_discord_count += 1
                else:
                    logger.warning(f"Роль с ID {role_id} не найдена в Discord, возможно уже удалена.")
            except Forbidden as e:
                logger.error(f"Бот не имеет прав на удаление роли с ID {role_id}: {e}", exc_info=True)
                errors.append({"role_id": role_id, "error": f"Нет прав на удаление: {e}"})
            except HTTPException as e:
                logger.error(f"Ошибка Discord API при удалении роли с ID {role_id}: {e}", exc_info=True)
                errors.append({"role_id": role_id, "error": f"Ошибка Discord API {e.status}: {e.message}"})
            except Exception as e:
                logger.error(f"Непредвиденная ошибка при удалении роли с ID {role_id} из Discord: {e}", exc_info=True)
                errors.append({"role_id": role_id, "error": f"Непредвиденная ошибка: {e}"})
        
        if role_ids:
            logger.info(f"Отправка {len(role_ids)} ролей на бэкенд для удаления из БД...")
            try:
                delete_response = await self.roles_mapping_api_client.delete_roles_by_discord_ids(guild_id, role_ids)
                
                # --- ИСПРАВЛЕНИЕ 2.3: Корректная проверка success-статуса для удаления ---
                if delete_response.get("success") is True: # Проверяем top-level "success" ключ
                    deleted_from_backend_count = delete_response.get("data", {}).get("deleted_count", 0)
                    logger.info(f"Удаление ролей из бэкенда завершено: {delete_response.get('message')}. Удалено: {deleted_from_backend_count}")
                else:
                    logger.error(f"Бэкенд вернул ошибку при удалении ролей из БД: {delete_response.get('message')}")
                    errors.append({"backend_delete": "Ошибка", "message": delete_response.get('message')})
            except (ConnectionError, ValueError, RuntimeError) as e:
                logger.error(f"Ошибка при удалении ролей из бэкенда: {e}", exc_info=True)
                errors.append({"backend_delete": "Ошибка", "message": str(e)})

        return {
            "status": "success" if not errors else "partial_success",
            "message": "Удаление ролей завершено." if not errors else "Удаление ролей завершено с ошибками.",
            "details": {
                "deleted_from_discord": deleted_from_discord_count,
                "deleted_from_backend": deleted_from_backend_count,
                "errors": errors
            }
        }
