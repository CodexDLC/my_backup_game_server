# game_server/app_discord_bot/storage/cache/managers/guild_config_manager.py
import json
import logging
from typing import Dict, Any, Optional, List
import inject

from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.guild_config_manager_interface import IGuildConfigManager

class GuildConfigManager(IGuildConfigManager):
    """
    Менеджер кэша для хранения конфигурации гильдий (шардов) в виде Redis Hash.
    Данные, хранящиеся здесь, являются постоянными.
    """
    ALLOWED_SHARD_TYPES = {"hub", "game"}
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger
        self.KEY_PATTERN = RedisKeys.GUILD_CONFIG_HASH
        self.logger.info("✨ GuildConfigManager (DI-ready) инициализирован.")
        
    async def _get_key(self, guild_id: int, shard_type: str) -> str:
        """Формирует ключ Redis для Hash конфигурации гильдии."""
        if shard_type not in GuildConfigManager.ALLOWED_SHARD_TYPES:
            raise ValueError(f"Недопустимый тип шарда: '{shard_type}'. Ожидается один из {GuildConfigManager.ALLOWED_SHARD_TYPES}.")
        return self.KEY_PATTERN.format(guild_id=guild_id, shard_type=shard_type)

    async def set_field(self, guild_id: int, field_name: str, data: Any, shard_type: str):
        """
        Устанавливает значение поля в Hash конфигурации гильдии.
        :param guild_id: ID гильдии Discord.
        :param field_name: Имя поля для установки.
        :param data: Данные для установки (будут сериализованы в JSON, если это dict/list).
        :param shard_type: Тип шарда ("hub" или "game").
        """
        key = await self._get_key(guild_id, shard_type)
        try:
            value = json.dumps(data) if isinstance(data, (dict, list)) else data
            await self.redis_client.hset(key, field_name, value)
            self.logger.debug(f"Поле '{field_name}' в Hash '{key}' установлено.")
        except Exception as e:
            self.logger.error(f"Ошибка при установке поля '{field_name}' в Hash '{key}': {e}", exc_info=True)

    async def get_field(self, guild_id: int, field_name: str, shard_type: str) -> Optional[Any]:
        """
        Извлекает одно поле из Hash конфигурации гильдии.
        :param guild_id: ID гильдии Discord.
        :param field_name: Имя поля для извлечения.
        :param shard_type: Тип шарда ("hub" или "game").
        :return: Значение поля или None, если не найдено.
        """
        key = await self._get_key(guild_id, shard_type)
        try:
            value = await self.redis_client.hget(key, field_name)
            if value:
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении поля '{field_name}' из Hash '{key}': {e}", exc_info=True)
            return None

    async def get_all_fields(self, guild_id: int, shard_type: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает все поля и их значения из Hash конфигурации гильдии.
        :param guild_id: ID гильдии Discord.
        :param shard_type: Тип шарда ("hub" или "game").
        :return: Словарь всех полей и значений или None, если Hash не найден.
        """
        key = await self._get_key(guild_id, shard_type)
        try:
            all_data = await self.redis_client.hgetall(key)
            if not all_data:
                self.logger.warning(f"Конфигурация для гильдии {guild_id} (ключ {key}) не найдена в кэше.")
                return None
            
            parsed_data = {}
            for field, value in all_data.items():
                try:
                    parsed_data[field] = json.loads(value) 
                except (json.JSONDecodeError, TypeError):
                    parsed_data[field] = value
            return parsed_data
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех полей из Hash '{key}': {e}", exc_info=True)
            return None

    async def delete_fields(self, guild_id: int, fields: List[str], shard_type: str) -> None:
        """
        Удаляет одно или несколько полей из Hash конфигурации гильдии.
        :param guild_id: ID гильдии Discord.
        :param fields: Список имен полей для удаления.
        :param shard_type: Тип шарда ("hub" или "game").
        """
        if not fields:
            return
        key = await self._get_key(guild_id, shard_type)
        try:
            await self.redis_client.hdel(key, *fields)
            self.logger.info(f"Поля {fields} удалены из Hash '{key}'.")
        except Exception as e:
            self.logger.error(f"Ошибка при удалении полей {fields} из Hash '{key}': {e}", exc_info=True)

    async def delete_config(self, guild_id: int, shard_type: str) -> None:
        """
        Полностью удаляет Hash конфигурации для гильдии.
        :param guild_id: ID гильдии Discord.
        :param shard_type: Тип шарда ("hub" или "game").
        """
        key = await self._get_key(guild_id, shard_type)
        try:
            await self.redis_client.delete(key)
            self.logger.info(f"Конфигурация (Hash) для гильдии {guild_id} (ключ '{key}') удалена из кэша.")
        except Exception as e:
            self.logger.error(f"Ошибка при удалении Hash '{key}': {e}", exc_info=True)

    # =========================================================================
    # НОВЫЙ МЕТОД: Атомарное добавление ID игрока в список зарегистрированных
    # =========================================================================
    async def add_player_id_to_registered_list(self, guild_id: int, shard_type: str, player_discord_id: str):
        """
        Атомарно добавляет Discord ID игрока в список зарегистрированных игроков для данного шарда,
        используя Lua-скрипт для обеспечения безопасности в конкурентной среде.
        """
        key = await self._get_key(guild_id, shard_type)
        field = RedisKeys.FIELD_REGISTERED_PLAYER_IDS
        
        lua_script = """
            local key = KEYS[1]
            local field = ARGV[1]
            local new_id = ARGV[2]

            local current_json = redis.call('HGET', key, field)
            local current_list = {}

            -- Проверяем, есть ли что-то в current_json и декодируем
            if current_json and current_json ~= '' then
                current_list = cjson.decode(current_json)
            end

            local found = false
            for i, v in ipairs(current_list) do
                if v == new_id then
                    found = true
                    break
                end
            end

            if not found then
                table.insert(current_list, new_id)
                redis.call('HSET', key, field, cjson.encode(current_list))
                return 1 -- ID добавлен
            else
                return 0 -- ID уже был в списке
            end
        """
        
        try:
            # 🔥 ИЗМЕНЕНО: Передаем ключи и аргументы как списки, как ожидает DiscordRedisClient.eval
            result = await self.redis_client.eval(lua_script, keys=[key], args=[field, player_discord_id])

            if result == 1:
                self.logger.debug(f"Игрок {player_discord_id} успешно добавлен в список {field} для гильдии {guild_id}.")
            else:
                self.logger.debug(f"Игрок {player_discord_id} уже был в списке {field} для гильдии {guild_id}, пропущено добавление.")
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении Lua-скрипта для добавления игрока {player_discord_id} в список для гильдии {guild_id}: {e}", exc_info=True)
            raise