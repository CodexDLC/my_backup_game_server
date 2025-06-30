# game_server/app_discord_bot/app/services/admin/role_management_service.py
from typing import Dict, Any, List, Optional
import discord
import uuid

from game_server.app_discord_bot.storage.cache.bot_cache_initializer import BotCache
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.app.services.utils.request_helper import RequestHelper
from game_server.common_contracts.api_models.discord_api import UnifiedEntitySyncRequest
from game_server.common_contracts.api_models.system_api import GetAllStateEntitiesRequest
from game_server.config.logging.logging_setup import app_logger as logger
from .base_discord_operations import BaseDiscordOperations
# Добавляем импорт CacheSyncManager
from game_server.app_discord_bot.app.services.utils.cache_sync_manager import CacheSyncManager


class RoleManagementService:
    """
    Сервисный слой для управления ролями Discord.
    Обеспечивает двустороннюю синхронизацию между БД и Discord.
    """
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(bot, 'request_helper'):
            logger.error("RequestHelper не инициализирован в объекте бота.")
            raise RuntimeError("RequestHelper не инициализирован.")
        self.request_helper: RequestHelper = bot.request_helper
        self.logger = logger
        self.base_ops = BaseDiscordOperations(bot)

        if not hasattr(bot, 'cache_manager') or not isinstance(bot.cache_manager, BotCache):
            logger.critical("BotCache не инициализирован в объекте бота.")
            raise RuntimeError("BotCache не инициализирован.")
        self.guild_config_manager = bot.cache_manager.guild_config

        # РЕФАКТОРИНГ: Получаем CacheSyncManager из объекта bot для синхронизации локального кэша с бэкендом
        if not hasattr(bot, 'sync_manager'):
            logger.critical("CacheSyncManager (sync_manager) не инициализирован в объекте бота. Убедитесь, что он настроен через UtilsInitializer в main.py.")
            raise RuntimeError("CacheSyncManager не инициализирован.")
        self.cache_sync_manager: CacheSyncManager = bot.sync_manager


    async def sync_discord_roles(self, guild_id: int, message: Optional[discord.Message] = None) -> Dict[str, Any]:
        """
        Синхронизирует роли Discord.
        1. Гарантирует наличие системных ролей из БД в Discord.
        2. Считывает ВСЕ роли из Discord.
        3. Отправляет полный список на бэкенд для upsert-синхронизации.
        4. Кэширует результат.
        5. Полностью синхронизирует локальный кэш гильдии с бэкенд-Redis.
        :param guild_id: ID гильдии Discord.
        :param message: Объект сообщения Discord для обновления прогресса (опционально).
        """
        guild = await self.base_ops.get_guild_by_id(guild_id)
        if not guild:
            raise ValueError(f"Discord сервер с ID {guild_id} не найден.")

        if message:
            await message.edit(content="Начинаю синхронизацию ролей: Получаю системные роли с бэкенда...")

        # --- Шаг 1: Получаем "ожидаемые" системные роли из бэкенда ---
        self.logger.info("Запрос системных ролей (State Entities) с бэкенда...")
        roles_to_process = []
        try:
            get_entities_payload = GetAllStateEntitiesRequest(guild_id=guild_id, entity_type="role")
            response_data, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.state_entity.get_all,
                request_payload=get_entities_payload,
                correlation_id=get_entities_payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "sync_roles_get_states"}
            )
            if not response_data or response_data.get("status") != "success":
                raise RuntimeError("Бэкенд вернул ошибку при получении State Entities.")
            
            # ВРЕМЕННОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ: Выводим полное тело response_data
            self.logger.critical(f"ДИАГНОСТИКА: Полное response_data от бэкенда (тип: {type(response_data)}): {response_data}")

            all_state_entities = response_data.get("data", {}).get("entities", [])
            
            # ВРЕМЕННОЕ ЛОГИРОВАНИЕ ДЛЯ ДИАГНОСТИКИ:
            self.logger.critical(f"ДИАГНОСТИКА: all_state_entities (тип: {type(all_state_entities)}, длина: {len(all_state_entities)}): {all_state_entities}")
            
            roles_to_process = [se for se in all_state_entities if se.get("ui_type") in ["access_level", "status_flag"]]
            self.logger.info(f"С бэкенда получено {len(roles_to_process)} системных ролей для проверки.")

            if message:
                await message.edit(content=f"Получено {len(roles_to_process)} системных ролей. Проверяю их наличие в Discord...")

        except Exception as e:
            self.logger.error(f"Не удалось получить системные роли с бэкенда: {e}", exc_info=True)
            if message:
                await message.edit(content=f"Ошибка: Не удалось получить системные роли с бэкенда. {e}")
            raise # Пробрасываем ошибку, чтобы она была обработана выше

        # Создаем словарь для быстрого поиска access_code
        access_code_map = {
            se.get('description'): se.get('access_code')
            for se in roles_to_process if se.get('description')
        }

        # --- Шаг 2: Гарантируем наличие системных ролей в Discord ---
        # Бот должен создавать все роли, которые он получает из базы сервера
        for role_name in access_code_map.keys():
            await self.base_ops.create_or_update_role(guild, role_name) # Это создаст роль, если её нет
        self.logger.info("Проверка и создание системных ролей в Discord завершены.")

        if message:
            await message.edit(content="Системные роли в Discord проверены и созданы. Считываю все роли с сервера...")

        # --- Шаг 3 - Считываем ВСЕ роли напрямую из Discord ---
        self.logger.info("Считывание всех ролей с сервера Discord...")
        all_discord_roles = guild.roles
        
        # --- Шаг 4 - Готовим ПОЛНЫЙ список для синхронизации ---
        entities_to_sync: List[Dict[str, Any]] = []
        for role in all_discord_roles:
            # Пропускаем стандартную роль @everyone
            if role.is_default():
                self.logger.debug(f"Пропускаем роль '{role.name}' (ID: {role.id}) - это @everyone.")
                continue
            # РЕФАКТОРИНГ (ДИАГНОСТИКА): Временно закомментируем проверку is_bot_managed() для отладки
            # if role.is_bot_managed():
            #     self.logger.debug(f"Пропускаем роль '{role.name}' (ID: {role.id}) - управляется ботом/интеграцией.")
            #     continue
            
            entities_to_sync.append({
                "discord_id": role.id,
                "entity_type": "role",
                "name": role.name,
                "access_code": access_code_map.get(role.name), # Добавляем access_code, если он есть в системных ролях
                "guild_id": guild_id,
                "description": None, 
                "parent_id": None, 
                "permissions": None
            })

        if message:
            await message.edit(content=f"Найдено {len(entities_to_sync)} ролей в Discord. Отправляю на синхронизацию с бэкендом...")

        # --- Шаг 5: Отправляем ПОЛНЫЙ список на бэкенд для upsert-синхронизации ---
        if not entities_to_sync:
            final_message_content = "На сервере не найдено ролей для синхронизации."
            if message:
                await message.edit(content=final_message_content)
            return {"status": "success", "message": final_message_content}

        self.logger.info(f"Отправка {len(entities_to_sync)} ролей на бэкенд для upsert-синхронизации...")
        sync_payload = UnifiedEntitySyncRequest(guild_id=guild_id, entities_data=entities_to_sync)
        
        try:
            sync_response, _ = await self.request_helper.send_and_await_response(
                api_method=self.request_helper.http_client_gateway.discord.sync_entities,
                request_payload=sync_payload,
                correlation_id=sync_payload.correlation_id,
                discord_context={"guild_id": guild_id, "command_source": "sync_roles_upsert"}
            )

            if not sync_response or sync_response.get("status") != "success":
                error_msg = sync_response.get('message') if sync_response else "Нет ответа от сервера"
                if message:
                    await message.edit(content=f"Ошибка синхронизации с бэкендом: {error_msg}")
                raise RuntimeError(f"Бэкенд вернул ошибку при синхронизации ролей: {error_msg}")
            
            # Этот лог теперь будет вызываться только при реальном успехе
            self.logger.success(f"Полная синхронизация ролей с бэкендом успешно завершена. Ответ: {sync_response.get('message')}")

            if message:
                created_count = sync_response.get('data', {}).get('created_count', 0)
                updated_count = sync_response.get('data', {}).get('updated_count', 0)
                await message.edit(content=f"Синхронизация с бэкендом завершена. Создано: {created_count}, Обновлено: {updated_count}. Кэширую данные...")

            # --- Шаг 6: Кэширование результата (локально) ---
            try:
                # Используем тот же самый полный список entities_to_sync для кэширования
                roles_to_cache = {
                    role_data["name"]: {
                        "discord_id": role_data["discord_id"],
                        "access_code": role_data.get("access_code")
                    }
                    for role_data in entities_to_sync
                }
                if roles_to_cache:
                    await self.guild_config_manager.set_field(
                        guild_id=guild_id,
                        field_name=RedisKeys.FIELD_SYSTEM_ROLES,
                        data=roles_to_cache
                    )
                    self.logger.success(f"Обновленные данные о ролях для гильдии {guild_id} сохранены в кэше.")
                else:
                    self.logger.warning(f"Нет данных о ролях для кэширования для гильдии {guild_id}.")

                if message:
                    await message.edit(content="Данные о ролях сохранены в локальном кэше. Запускаю полную синхронизацию кэша с бэкендом...")

                # --- РЕФАКТОРИНГ: Шаг 7: Запускаем синхронизацию полной конфигурации гильдии с бэкендом ---
                self.logger.info(f"Запускаем синхронизацию полной конфигурации гильдии {guild_id} с бэкендом через CacheSyncManager после синхронизации ролей...")
                sync_success_to_backend = await self.cache_sync_manager.sync_guild_config_to_backend(guild_id)
                if sync_success_to_backend:
                    self.logger.success(f"Полная конфигурация гильдии {guild_id} успешно синхронизирована с бэкендом после синхронизации ролей.")
                else:
                    self.logger.error(f"Ошибка при синхронизации полной конфигурации гильдии {guild_id} с бэкендом после синхронизации ролей.")
                
                if message:
                    if sync_success_to_backend:
                        await message.edit(content="Полная конфигурация кэша успешно синхронизирована с бэкендом.")
                    else:
                        await message.edit(content="Ошибка: Полная конфигурация кэша не синхронизирована с бэкендом.")

            except Exception as e:
                self.logger.error(f"Не удалось закэшировать роли для гильдии {guild_id} или синхронизировать с бэкендом: {e}", exc_info=True)
                if message:
                    await message.edit(content=f"Ошибка: Не удалось закэшировать роли или синхронизировать кэш с бэкендом. {e}")
                raise # Пробрасываем ошибку

            return {"status": "success", "message": "Синхронизация ролей завершена.", "details": sync_response.get('data')}
        
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при синхронизации ролей: {e}", exc_info=True)
            if message:
                await message.edit(content=f"Критическая ошибка при синхронизации ролей: {e}")
            raise
