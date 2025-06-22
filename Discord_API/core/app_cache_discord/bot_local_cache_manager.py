# Discord_API/app_cache/bot_local_cache_manager.py

import json
from typing import Any, Dict, List, Optional
import logging



# 🔥 ИЗМЕНЕНИЕ: Импортируем ВСЕ необходимые константы из локального файла констант
from Discord_API.core.app_cache_discord.redis_constants import (
    KEY_PREFIX_USERS,
    KEY_PREFIX_CHANNELS_CONTEXT,
    KEY_PREFIX_DISPLAYED_ITEMS,
    KEY_PREFIX_REF_DATA, # На случай, если боту потребуется доступ к глобальным константам через менеджер

    KEY_FILE_USER_PROFILE,
    KEY_FILE_USER_STATUS_FLAGS,
    KEY_FILE_USER_CHARACTER_SNAPSHOT,
    KEY_FILE_USER_INVENTORY_SNAPSHOT,
    KEY_FILE_USER_GROUP_SNAPSHOT,
    KEY_FILE_USER_CHANNEL_IDS_LIST,

    DEFAULT_TTL_USER_CONTEXT,
    DEFAULT_TTL_CHANNEL_CONTEXT,
    DEFAULT_TTL_DISPLAYED_ITEM,
    DEFAULT_TTL_REF_DATA # Для глобальных данных
)
from Discord_API.core.app_cache_discord import discord_redis_client

logger = logging.getLogger("bot_cache_manager")

class BotLocalCacheManager:
    def __init__(self, redis_client=discord_redis_client):
        self.redis = redis_client

    # --- Методы для работы с основным контекстом пользователя (profile) ---
    async def get_user_profile(self, discord_account_id: str) -> Optional[Dict[str, Any]]:
        """Получает профиль пользователя из локального кэша."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_PROFILE}"
        return await self.redis.get_json(key)

    async def set_user_profile(self, discord_account_id: str, profile_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        """Сохраняет или обновляет профиль пользователя в локальном кэше."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_PROFILE}"
        await self.redis.set_json(key, profile_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен профиль пользователя {discord_account_id} в локальном Redis.")

    async def delete_user_profile(self, discord_account_id: str):
        """Удаляет профиль пользователя из локального кэша."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_PROFILE}"
        await self.redis.delete(key)
        logger.info(f"Удален профиль пользователя {discord_account_id} из локального Redis.")

    # --- Методы для работы со статусом персонажа (status_flags) ---
    async def get_character_status_flags(self, discord_account_id: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_STATUS_FLAGS}"
        return await self.redis.get_json(key)

    async def set_character_status_flags(self, discord_account_id: str, status_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_STATUS_FLAGS}"
        await self.redis.set_json(key, status_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлены флаги статуса персонажа {discord_account_id}.")

    # --- Методы для работы со снапшотами (character_snapshot) ---
    async def get_character_snapshot(self, discord_account_id: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_CHARACTER_SNAPSHOT}"
        return await self.redis.get_json(key)

    async def set_character_snapshot(self, discord_account_id: str, snapshot_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        """Сохраняет или обновляет полный снапшот персонажа (полученный по WS)."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_CHARACTER_SNAPSHOT}"
        await self.redis.set_json(key, snapshot_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен снапшот персонажа {discord_account_id} в локальном Redis.")

    # --- Методы для работы с инвентарем (inventory_snapshot) ---
    async def get_inventory_snapshot(self, discord_account_id: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_INVENTORY_SNAPSHOT}"
        return await self.redis.get_json(key)

    async def set_inventory_snapshot(self, discord_account_id: str, snapshot_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        """Сохраняет или обновляет снапшот инвентаря персонажа."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_INVENTORY_SNAPSHOT}"
        await self.redis.set_json(key, snapshot_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен снапшот инвентаря персонажа {discord_account_id} в локальном Redis.")

    # --- Методы для работы с группой (group_snapshot) ---
    async def get_group_snapshot(self, discord_account_id: str) -> Optional[Dict[str, Any]]:
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_GROUP_SNAPSHOT}"
        return await self.redis.get_json(key)

    async def set_group_snapshot(self, discord_account_id: str, snapshot_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        """Сохраняет или обновляет снапшот группы."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_GROUP_SNAPSHOT}"
        await self.redis.set_json(key, snapshot_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен снапшот группы для {discord_account_id} в локальном Redis.")

    # --- Методы для работы со списком каналов (channel_ids) ---
    async def get_user_channel_ids(self, discord_account_id: str) -> List[str]:
        """Получает список ID каналов пользователя."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_CHANNEL_IDS_LIST}"
        channel_ids_json = await self.redis.get_json(key)
        return channel_ids_json if isinstance(channel_ids_json, list) else []

    async def set_user_channel_ids(self, discord_account_id: str, channel_ids: List[str], ttl_seconds: Optional[int] = DEFAULT_TTL_USER_CONTEXT):
        """Сохраняет список ID каналов пользователя."""
        key = f"{KEY_PREFIX_USERS}:{discord_account_id}:{KEY_FILE_USER_CHANNEL_IDS_LIST}"
        await self.redis.set_json(key, channel_ids)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен список каналов для пользователя {discord_account_id}.")

    # --- Методы для работы с контекстом конкретного канала ---
    async def get_channel_context(self, discord_account_id: str, channel_id: str) -> Optional[Dict[str, Any]]:
        """Получает контекст конкретного канала."""
        # KEY_PREFIX_CHANNELS_CONTEXT должен быть форматируемой строкой
        key = f"{KEY_PREFIX_CHANNELS_CONTEXT.format(discord_account_id=discord_account_id)}:{channel_id}"
        return await self.redis.get_json(key)

    async def set_channel_context(self, discord_account_id: str, channel_id: str, context_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_CHANNEL_CONTEXT):
        """Сохраняет или обновляет контекст конкретного канала."""
        key = f"{KEY_PREFIX_CHANNELS_CONTEXT.format(discord_account_id=discord_account_id)}:{channel_id}"
        await self.redis.set_json(key, context_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен контекст канала {channel_id} для пользователя {discord_account_id}.")

    async def delete_channel_context(self, discord_account_id: str, channel_id: str):
        """Удаляет контекст конкретного канала."""
        key = f"{KEY_PREFIX_CHANNELS_CONTEXT.format(discord_account_id=discord_account_id)}:{channel_id}"
        await self.redis.delete(key)
        logger.info(f"Удален контекст канала {channel_id} для пользователя {discord_account_id}.")

    # --- Методы для работы с отображаемыми предметами ---
    async def get_displayed_item_context(self, discord_account_id: str, item_uuid: str) -> Optional[Dict[str, Any]]:
        """Получает контекст отображаемого предмета."""
        # KEY_PREFIX_DISPLAYED_ITEMS должен быть форматируемой строкой
        key = f"{KEY_PREFIX_DISPLAYED_ITEMS.format(discord_account_id=discord_account_id)}:{item_uuid}"
        return await self.redis.get_json(key)

    async def set_displayed_item_context(self, discord_account_id: str, item_uuid: str, item_data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_DISPLAYED_ITEM):
        """Сохраняет или обновляет контекст отображаемого предмета."""
        key = f"{KEY_PREFIX_DISPLAYED_ITEMS.format(discord_account_id=discord_account_id)}:{item_uuid}"
        await self.redis.set_json(key, item_data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлен контекст отображаемого предмета {item_uuid} для пользователя {discord_account_id}.")

    async def delete_displayed_item_context(self, discord_account_id: str, item_uuid: str):
        """Удаляет контекст отображаемого предмета."""
        key = f"{KEY_PREFIX_DISPLAYED_ITEMS.format(discord_account_id=discord_account_id)}:{item_uuid}"
        await self.redis.delete(key)
        logger.info(f"Удален контекст отображаемого предмета {item_uuid} для пользователя {discord_account_id}.")

    # --- Методы для работы с глобальными справочными данными ---
    async def get_global_ref_data(self, data_type: str, item_id: str) -> Optional[Dict[str, Any]]:
        """Получает глобальные справочные данные (например, шаблон предмета, навык)."""
        key = f"{KEY_PREFIX_REF_DATA}:{data_type}:{item_id}"
        return await self.redis.get_json(key)

    async def set_global_ref_data(self, data_type: str, item_id: str, data: Dict[str, Any], ttl_seconds: Optional[int] = DEFAULT_TTL_REF_DATA):
        """Сохраняет глобальные справочные данные."""
        key = f"{KEY_PREFIX_REF_DATA}:{data_type}:{item_id}"
        await self.redis.set_json(key, data)
        if ttl_seconds is not None:
            await self.redis.expire(key, ttl_seconds)
        logger.debug(f"Обновлены глобальные справочные данные {data_type}:{item_id}.")


# Создаем единственный экземпляр менеджера для использования в боте
bot_local_cache_manager = BotLocalCacheManager()