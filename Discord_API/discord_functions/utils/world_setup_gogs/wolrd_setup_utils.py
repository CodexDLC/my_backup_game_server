import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
import discord
from typing import Tuple # <-- ЭТО ПРАВИЛЬНО


from Discord_API.api_route_function.spec_route.discord_bindings_api import DiscordAPIClientError, get_all_discord_bindings_api
from Discord_API.api_route_function.system.system_gameworld_api import get_current_world

from Discord_API.config.logging.logging_setup import logger

from Discord_API.api_route_function.system.system_gameworld_api import get_all_regions, get_current_world, get_subregions






# --- Вспомогательная функция: Получение и структурирование привязок из БД ---
async def _get_existing_db_bindings_maps(guild_id: int) -> Tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, str]]:
    """
    Получает все Discord-привязки из базы данных для указанной гильдии
    и преобразует их в карты для быстрого поиска.

    Args:
        guild_id (int): ID гильдии Discord.

    Returns:
        Tuple[Dict[str, Dict], Dict[str, Dict], Dict[str, str]]: Кортеж из трёх словарей:
        - existing_category_bindings_map: {access_key_региона: полные_данные_привязки_категории}
        - existing_channel_bindings_map: {access_key_субрегиона: полные_данные_привязки_канала}
        - parent_access_key_to_discord_category_id_map: {access_key_региона: Discord_category_id}
                                                         (для существующих категорий)

    Raises:
        DiscordAPIClientError: Если произошла ошибка при получении данных от API.
    """
    logger.info(f"Запрос существующих привязок из БД для гильдии {guild_id}.")
    
    existing_db_bindings: List[Dict[str, Any]] = []
    try:
        existing_db_bindings = await get_all_discord_bindings_api(guild_id)
        logger.debug(f"Получено {len(existing_db_bindings)} привязок из БД.")
    except DiscordAPIClientError as e:
        logger.error(f"Ошибка при получении существующих привязок из БД: {e}", exc_info=True)
        raise # Перевыбрасываем, чтобы вызывающая функция могла обработать

    existing_category_bindings_map: Dict[str, Dict[str, Any]] = {}
    existing_channel_bindings_map: Dict[str, Dict[str, Any]] = {}
    parent_access_key_to_discord_category_id_map: Dict[str, str] = {}

    for binding in existing_db_bindings:
        db_access_key = binding.get("access_key")
        db_category_id = binding.get("category_id")
        db_channel_id = binding.get("channel_id")

        if db_access_key:
            # Если это привязка категории (есть category_id, но нет channel_id)
            if db_category_id and not db_channel_id:
                existing_category_bindings_map[db_access_key] = binding
                if db_category_id is not None:
                    parent_access_key_to_discord_category_id_map[db_access_key] = str(db_category_id)
            # Если это привязка канала (есть channel_id)
            elif db_channel_id:
                existing_channel_bindings_map[db_access_key] = binding
            else:
                logger.warning(f"Привязка из БД с неопределенным типом (нет category_id/channel_id, access_key={db_access_key}): {binding}")
        else:
            logger.warning(f"Привязка из БД без 'access_key': {binding}")

    logger.debug(f"Сформированы карты привязок: Категорий - {len(existing_category_bindings_map)}, Каналов - {len(existing_channel_bindings_map)}.")
    return existing_category_bindings_map, existing_channel_bindings_map, parent_access_key_to_discord_category_id_map

# --- Ваши существующие функции, не измененные на этом шаге: ---

def build_binding_batch(bindings_info: List[Dict]) -> List[Dict]:
    """Собирает пакет данных для массовой вставки, включая `guild_id`."""
    binding_batch = []
    for info in bindings_info:
        logger.debug(f"ℹ️ `datetime` сейчас: {datetime}") # Заменил print на logger
        logger.debug(f"🚀 UTC-время: {datetime.now(timezone.utc).isoformat()}") # Заменил print на logger
        binding_data = {
            "guild_id": info["guild_id"],  
            "world_id": str(info.get("world_id", uuid.uuid4())),  
            "access_key": info.get("access_key", "default_key"),
            "permissions": info.get("permissions", 0),
            "category_id": info.get("category_id"),
            "channel_id": info.get("channel_id"),
            "category_name": info.get("category_name"), # Добавил для полноты, если используется
            "channel_name": info.get("channel_name"),   # Добавил для полноты, если используется
            "description": info.get("description", "") # Добавил для полноты, если используется
        }
        logger.debug(f"📌 Добавлена привязка в пакет: {binding_data}") # Заменил print на logger
        binding_batch.append(binding_data)
    return binding_batch


async def collect_world_data():
    """Запрашивает мир, регионы и подрегионы, собирает их в память и возвращает структурированные данные."""
    
    logger.info("🚀 Запуск `collect_world_data()`...")

    world_data = await get_current_world()
    logger.debug(f"🔍 Данные мира: {world_data}")
    
    if not world_data or "world_id" not in world_data:
        logger.error("🚨 Ошибка: Мир не найден!")
        return None

    world_id = world_data["world_id"]
    
    all_regions = await get_all_regions()
    logger.debug(f"🔍 Все регионы: {all_regions}")

    regions = [region for region in all_regions if region.get("world_id") == world_id]
    logger.debug(f"✅ Фильтрованные регионы: {regions}")

    all_subregions = await get_subregions()
    logger.info(f"DEBUG: Сырые данные из get_subregions(): {all_subregions}") # Добавьте это
    
    logger.debug(f"Всего подрегионов из базы: {len(all_subregions)}")
    # logger.debug(f"🔍 Все подрегионы (подробно): {all_subregions}") # Если нужен полный вывод через логгер

    subregions_map = {
        region["access_key"]: [
            subregion for subregion in all_subregions if subregion["parent_access_key"] == region["access_key"]
        ]
        for region in regions
    }
    logger.debug(f"✅ Привязка регионов к подрегионам: {subregions_map}")

    collected_data = {
        "world_id": world_id,
        "world_name": world_data["world_name"],
        "regions": regions,
        "subregions": subregions_map
    }
    
    logger.debug(f"📊 Размер `regions`: {len(regions)}, `subregions_map`: {sum(len(v) for v in subregions_map.values())}")
    logger.info("✅ Данные загружены успешно!")

    return collected_data


async def create_category_if_not_exists(guild: discord.Guild, region_name: str) -> discord.CategoryChannel:
    """Создает категорию для региона, если её нет."""
    
    logger.info(f"🚀 Проверяем категорию: {region_name}") # Заменил print на logger

    category = discord.utils.get(guild.categories, name=region_name)
    
    if category:
        logger.info(f"✅ Категория уже существует: {category.name} (ID: {category.id})") # Заменил print на logger
    else:
        logger.warning(f"⚠️ Категория не найдена, создаем новую: {region_name}") # Заменил print на logger
        category = await guild.create_category(name=region_name)
        
    return category

async def create_text_channel_if_not_exists(category: discord.CategoryChannel, subregion_name: str, description: str) -> discord.TextChannel:
    """Создает текстовый канал для подрегиона, если он отсутствует."""
    
    channel = discord.utils.get(category.text_channels, name=subregion_name)
    
    if not channel:
        logger.info(f"⚠️ Канал '{subregion_name}' не найден в категории '{category.name}', создаем новый.")
        channel = await category.create_text_channel(name=subregion_name, topic=description)
        logger.info(f"✅ Канал '{subregion_name}' (ID: {channel.id}) создан в категории '{category.name}'.")
    else:
        logger.info(f"✅ Канал '{subregion_name}' (ID: {channel.id}) уже существует в категории '{category.name}'.")
    
    return channel


async def _prepare_category_bindings_for_upsert(
    collected_data: Dict[str, Any], 
    existing_category_bindings_map: Dict[str, Dict[str, Any]],
    # Добавляем этот параметр, чтобы передать map для заполнения
    parent_access_key_to_discord_category_id_map: Dict[str, str] 
) -> List[Dict[str, Any]]:
    """
    Определяет, какие привязки Discord-категорий (регионов) отсутствуют в базе данных,
    и подготавливает их для UPSERT. Также заполняет карту Discord category_id для
    существующих категорий.

    Args:
        collected_data (Dict[str, Any]): Словарь с данными о мире и регионах.
        existing_category_bindings_map (Dict[str, Dict[str, Any]]): Карта существующих
                                                                    привязок категорий из БД.
        parent_access_key_to_discord_category_id_map (Dict[str, str]): Карта, которая
                                                                      будет заполнена access_key региона
                                                                      и его Discord category_id для существующих привязок.

    Returns:
        List[Dict[str, Any]]: Список данных для привязок категорий, которые необходимо создать/обновить.
    """
    logger.info("Подготовка привязок категорий для UPSERT.")
    
    regions = collected_data.get("regions", [])
    world_id = collected_data.get("world_id")
    
    bindings_to_upsert: List[Dict[str, Any]] = []
    
    for region in regions:
        region_access_key = region["access_key"]
        region_name = region["region_name"]
        
        if region_access_key not in existing_category_bindings_map:
            # Если привязки категории нет в БД, добавляем её для создания
            logger.debug(f"Привязка категории '{region_name}' (Access Key: '{region_access_key}') отсутствует в БД. Добавляем в список UPSERT.")
            bindings_to_upsert.append({
                "guild_id": None, # guild_id будет добавлен на более высоком уровне
                "world_id": world_id,
                "access_key": region_access_key,
                "permissions": 0,
                "category_id": None, # Discord ID будет получен после создания категории в Discord
                "channel_id": None, 
                "category_name": region_name,
                "description": region.get("description", "")
            })
        else:
            # Если привязка категории УЖЕ ЕСТЬ в БД, то берём её Discord ID
            # и сохраняем в карту для использования при обработке каналов.
            db_binding = existing_category_bindings_map[region_access_key]
            if "category_id" in db_binding and db_binding["category_id"] is not None:
                parent_access_key_to_discord_category_id_map[region_access_key] = str(db_binding["category_id"])
                logger.debug(f"Существующая категория '{region_name}' (Access Key: '{region_access_key}') имеет Discord ID: {db_binding['category_id']}.")
            else:
                logger.warning(f"Существующая привязка категории '{region_name}' (Access Key: '{region_access_key}') не содержит Discord category_id. "
                               f"Она может быть неполной, каналы для неё не будут привязаны к Discord ID.")

    logger.info(f"Подготовлено {len(bindings_to_upsert)} новых привязок категорий для UPSERT. Заполнено {len(parent_access_key_to_discord_category_id_map)} Discord category_id для существующих категорий.")
    return bindings_to_upsert




async def get_bindings_to_create_or_update(guild_id: int, collected_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Координирует процесс определения всех привязок Discord (категорий и каналов),
    которые необходимо создать или обновить в базе данных.

    Args:
        guild_id (int): ID гильдии Discord.
        collected_data (Dict[str, Any]): Словарь с данными о мире, регионах и субрегионах,
                                       полученными из collect_world_data().

    Returns:
        List[Dict[str, Any]]: Единый список словарей, представляющих привязки,
                              готовые для массового UPSERT.
    """
    logger.info(f"Запуск `get_bindings_to_create_or_update` для guild_id={guild_id}.")

    # 1. Получаем и структурируем существующие привязки из БД
    existing_category_bindings_map, existing_channel_bindings_map, parent_access_key_to_discord_category_id_map = \
        await _get_existing_db_bindings_maps(guild_id)

    all_bindings_to_upsert: List[Dict[str, Any]] = []

    # 2. Подготавливаем привязки категорий
    # Передаём карту для заполнения category_id существующих категорий
    category_bindings_for_upsert = await _prepare_category_bindings_for_upsert(
        collected_data,
        existing_category_bindings_map,
        parent_access_key_to_discord_category_id_map # Передаем ссылку на ту же карту
    )
    all_bindings_to_upsert.extend(category_bindings_for_upsert)
    
    # 3. Подготавливаем привязки каналов
    # Карта parent_access_key_to_discord_category_id_map теперь заполнена Discord ID
    # для существующих категорий.
    channel_bindings_for_upsert = await _prepare_channel_bindings_for_upsert(
        collected_data,
        existing_channel_bindings_map,
        parent_access_key_to_discord_category_id_map
    )
    all_bindings_to_upsert.extend(channel_bindings_for_upsert)

    # 4. Добавляем guild_id ко всем элементам в итоговом списке
    # Это удобно сделать здесь, чтобы не передавать guild_id в каждую вспомогательную функцию
    for binding_data in all_bindings_to_upsert:
        if "guild_id" not in binding_data or binding_data["guild_id"] is None:
            binding_data["guild_id"] = guild_id
    
    logger.info(f"Всего подготовлено {len(all_bindings_to_upsert)} привязок для UPSERT.")
    return all_bindings_to_upsert


async def _prepare_channel_bindings_for_upsert(
    collected_data: Dict[str, Any],
    existing_channel_bindings_map: Dict[str, Dict[str, Any]],
    parent_access_key_to_discord_category_id_map: Dict[str, str]
) -> List[Dict[str, Any]]:
    logger.info("Подготовка привязок каналов для UPSERT.")
    
    # --- ДОБАВЛЕННЫЕ ЛОГИ ---
    logger.debug(f"DEBUG: collected_data получены в _prepare_channel_bindings_for_upsert: {collected_data}")
    # ^^^ Этот лог покажет весь словарь collected_data
    
    world_id = collected_data.get("world_id")
    subregions_map = collected_data.get("subregions", {}) # <-- Здесь берется subregions_map
    
    logger.debug(f"DEBUG: subregions_map, извлеченный из collected_data: {subregions_map}")
    # ^^^ Этот лог покажет, что находится в subregions_map после извлечения
    # --- КОНЕЦ ДОБАВЛЕННЫХ ЛОГОВ ---

    bindings_to_upsert: List[Dict[str, Any]] = []

    for parent_ak, subregions in subregions_map.items():
        discord_category_id_for_parent = parent_access_key_to_discord_category_id_map.get(parent_ak)

        if not discord_category_id_for_parent:
            logger.warning(f"Пропускаем субрегионы для родительского access_key='{parent_ak}', "
                            f"так как соответствующая Discord категория ещё не привязана (нет category_id в БД).")
            continue

        for subregion in subregions:
            subregion_access_key = subregion["access_key"]
            subregion_name = subregion["subregion_name"]

            if subregion_access_key not in existing_channel_bindings_map:
                logger.debug(f"Привязка канала '{subregion_name}' (Access Key: '{subregion_access_key}') отсутствует в БД. Добавляем в список UPSERT.")
                bindings_to_upsert.append({
                    "guild_id": None,
                    "world_id": world_id,
                    "access_key": subregion_access_key,
                    "permissions": 0,
                    "category_id": discord_category_id_for_parent,
                    "channel_id": None,
                    "channel_name": subregion_name,
                    "description": subregion.get("description", ""),
                    "parent_access_key": parent_ak
                })

    logger.info(f"Подготовлено {len(bindings_to_upsert)} новых привязок каналов для UPSERT.")
    return bindings_to_upsert