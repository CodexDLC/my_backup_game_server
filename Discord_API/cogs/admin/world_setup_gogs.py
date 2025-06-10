# cogs/setup_world_system_cog.py (пример пути к файлу)
from typing import Any, Dict, List
import discord
from discord.ext import commands
import asyncio 

# Предполагаемые импорты на основе наших предыдущих обсуждений и структуры вашего проекта
from Discord_API.api_route_function.spec_route.discord_bindings_api import DiscordAPIClientError, upsert_discord_bindings_api
# Предполагаем, что create_roles_discord предназначен для операций с БД, а не для создания через Discord API
from Discord_API.config.logging.logging_setup import logger

# Утилиты, специфичные для настройки мира.
from Discord_API.discord_functions.utils.world_setup_gogs.setup_roles_utils import send_and_delete_temp_message

# ВАЖНО: Обновите эти импорты, чтобы они указывали на ваш файл,
# где находятся новые вспомогательные функции, например:
from Discord_API.discord_functions.utils.world_setup_gogs.wolrd_setup_utils import (
    _prepare_category_bindings_for_upsert,
    _prepare_channel_bindings_for_upsert,
    collect_world_data, # Уже есть
    _get_existing_db_bindings_maps,
     # Новая функция, которую мы добавили
)
from Discord_API.discord_functions.world_setup import _process_discord_categories_creation, _process_discord_channels_creation


## Ког SetupWorldSystem
## Ког SetupWorldSystem

class SetupWorldSystem(commands.Cog):
    """Ког для создания и управления структурой игрового мира в Discord."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    ### Команда `setup_world`

    @commands.command(name="setup_world", aliases=["SW"])
    @commands.has_permissions(administrator=True)
    async def setup_world(self, ctx: commands.Context):
        """Запускает процесс создания категорий и каналов в Discord на основе данных мира."""

        logger.info(f"🔧 [СТАРТ] Команда `setup_world()` запущена пользователем {ctx.author} в гильдии '{ctx.guild.name}' ({ctx.guild.id}).")
        
        await send_and_delete_temp_message(ctx.channel, "🔧 **Запуск настройки мира...**")

        # 1️⃣ **Собираем данные мира**
        logger.info("📌 [ШАГ 1] Сбор данных мира из API...")
        logger.info("📌 [ШАГ 1] Сбор данных мира из API...")
        try:
            collected_data = await collect_world_data()
            # 🔥🔥🔥 ВОТ ЭТА СТРОКА ЛОГИРОВАНИЯ 🔥🔥🔥
            logger.debug(f"DEBUG: Полные данные, полученные от collect_world_data: {collected_data}")
            # 🔥🔥🔥 КОНЕЦ БЛОКА ЛОГИРОВАНИЯ 🔥🔥🔥

            if not collected_data:
                logger.error("❌ [ОШИБКА] Мир не найден или API для сбора данных мира недоступен.")
                await ctx.send("❌ **Ошибка:** данные мира не найдены или сервис API недоступен.")
                return
            logger.info(f"🌍 [ШАГ 1] Данные мира успешно получены: {collected_data.get('world_name', 'Неизвестный мир')}")
            await ctx.send(f"🌍 **Настройка мира:** `{collected_data.get('world_name', 'Неизвестный мир')}`")
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Ошибка при сборе данных мира: {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Не удалось собрать данные мира. Детали: {e}")
            return

        # 2️⃣ **Получаем существующие привязки и готовим привязки категорий (initial)**
        logger.info("📌 [ШАГ 2] Получение существующих привязок из БД и подготовка категорий...")
        category_bindings_to_process: List[Dict[str, Any]] = [] # Это будет список категорий, которые нужно обработать
        existing_category_bindings_map: Dict[str, Dict[str, Any]] = {}
        existing_channel_bindings_map: Dict[str, Dict[str, Any]] = {}
        current_discord_category_ids_map: Dict[str, str] = {} # Карта для хранения Discord ID категорий

        try:
            # Получаем все существующие привязки из БД
            # current_discord_category_ids_map здесь будет заполнена ID *существующих* категорий
            existing_category_bindings_map, existing_channel_bindings_map, current_discord_category_ids_map = \
                await _get_existing_db_bindings_maps(ctx.guild.id)
            
            # Подготавливаем привязки категорий (только категорий, без каналов на этом этапе)
            category_bindings_to_process = await _prepare_category_bindings_for_upsert(
                collected_data,
                existing_category_bindings_map,
                current_discord_category_ids_map # Передаем эту карту, она уже содержит ID существующих
            )

            if not category_bindings_to_process and not existing_channel_bindings_map: # Проверяем, есть ли что-то вообще
                logger.info("✅ [ШАГ 2] Нет новых категорий или каналов для создания/обновления. Все привязки актуальны.")
                await ctx.send("✅ **Все категории и каналы уже актуальны. Ничего нового создавать не нужно.**")
                return 
            
            logger.info(f"📊 [ШАГ 2] Найдено {len(category_bindings_to_process)} категорий для обработки.")
        except DiscordAPIClientError as e:
            logger.error(f"❌ [ОШИБКА] Ошибка при получении/обработке существующих привязок из БД: {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Не удалось определить привязки из базы данных. Детали: {e}")
            return
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Непредвиденная ошибка при подготовке категорий: {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Произошла непредвиденная ошибка при подготовке категорий. Детали: {e}")
            return
        
        # 🔥🔥🔥 Теперь current_discord_category_ids_map содержит ID категорий, которые УЖЕ БЫЛИ в БД
        
        # 3️⃣ **Создаём недостающие категории Discord и обновляем их ID в привязках**
        logger.info("📌 [ШАГ 3] Создание/проверка категорий Discord...")
        updated_category_bindings: List[Dict[str, Any]] = []
        try:
            updated_category_bindings = await _process_discord_categories_creation(
                ctx.guild, 
                category_bindings_to_process # Список привязок категорий
            )
            # Обновляем карту `current_discord_category_ids_map` созданными ID категорий
            for binding in updated_category_bindings:
                if binding.get("access_key") and binding.get("category_id"):
                    current_discord_category_ids_map[binding["access_key"]] = binding["category_id"]

            logger.info(f"📦 [ШАГ 3] Обработано {len(updated_category_bindings)} категорий. "
                         f"Создано {len([b for b in updated_category_bindings if b['category_id'] is not None and b['access_key'] not in existing_category_bindings_map])} новых Discord категорий.")
        except discord.Forbidden:
            logger.error(f"❌ [ОШИБКА] Боту не хватает прав для создания категорий в гильдии '{ctx.guild.name}'.")
            await ctx.send("❌ Ошибка прав: У меня недостаточно разрешений для создания категорий. Проверьте мои разрешения.")
            return
        except discord.HTTPException as e:
            logger.error(f"❌ [ОШИБКА] Ошибка API Discord при создании категорий (статус: {e.status}, текст: {e.text}): {e}", exc_info=True)
            await ctx.send(f"❌ Произошла ошибка связи с Discord API при создании категорий. Детали: {e.text}")
            return
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Непредвиденная ошибка при создании категорий: {e}", exc_info=True)
            await ctx.send(f"❌ Произошла непредвиденная ошибка при создании категорий. Детали: {e}")
            return

        # 🔥🔥🔥 НОВЫЙ ШАГ (4) - Теперь, когда current_discord_category_ids_map ПОЛНАЯ, готовим каналы 🔥🔥🔥
        logger.info("📌 [ШАГ 4] Подготовка привязок каналов (после создания категорий)...")
        channel_bindings_to_process: List[Dict[str, Any]] = []
        try:
            channel_bindings_to_process = await _prepare_channel_bindings_for_upsert(
                collected_data,
                existing_channel_bindings_map, # Передаем существующие привязки каналов
                current_discord_category_ids_map # ЭТА КАРТА ТЕПЕРЬ СОДЕРЖИТ ВСЕ НУЖНЫЕ DISCORD ID КАТЕГОРИЙ!
            )
            logger.info(f"📊 [ШАГ 4] Подготовлено {len(channel_bindings_to_process)} привязок каналов для обработки.")
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Непредвиденная ошибка при подготовке привязок каналов: {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Произошла непредвиденная ошибка при подготовке привязок каналов. Детали: {e}")
            return


        # 5️⃣ **Создаём недостающие каналы Discord и обновляем их ID в привязках**
        logger.info("📌 [ШАГ 5] Создание/проверка текстовых каналов Discord...")
        updated_channel_bindings: List[Dict[str, Any]] = []
        try:
            updated_channel_bindings = await _process_discord_channels_creation(
                ctx.guild,
                channel_bindings_to_process, # Список привязок каналов с channel_id=None
                current_discord_category_ids_map # Карта, содержащая Discord ID категорий
            )
            logger.info(f"📦 [ШАГ 5] Обработано {len(updated_channel_bindings)} каналов. "
                         f"Создано {len([b for b in updated_channel_bindings if b['channel_id'] is not None])} новых Discord каналов.")
        except discord.Forbidden:
            logger.error(f"❌ [ОШИБКА] Боту не хватает прав для создания каналов в гильдии '{ctx.guild.name}'.")
            await ctx.send("❌ Ошибка прав: У меня недостаточно разрешений для создания каналов. Проверьте мои разрешения.")
            return
        except discord.HTTPException as e:
            logger.error(f"❌ [ОШИБКА] Ошибка API Discord при создании каналов (статус: {e.status}, текст: {e.text}): {e}", exc_info=True)
            await ctx.send(f"❌ Произошла ошибка связи с Discord API при создании каналов. Детали: {e.text}")
            return
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Непредвиденная ошибка при создании каналов: {e}", exc_info=True)
            await ctx.send(f"❌ Произошла непредвиденная ошибка при создании каналов. Детали: {e}")
            return
        
        # 6️⃣ **Объединяем все обновленные привязки для массового UPSERT**
        final_bindings_for_upsert = updated_category_bindings + updated_channel_bindings
        
        logger.info(f"📊 [ШАГ 6] Всего привязок для окончательного UPSERT в БД: {len(final_bindings_for_upsert)}")

        # 🔥🔥🔥 НОВЫЙ БЛОК: ДОБАВЛЯЕМ guild_id КО ВСЕМ ПРИВЯЗКАМ 🔥🔥🔥
        # Получаем guild_id из контекста команды
        # Важно: Discord IDs очень большие, они могут быть строками или BIGINT в БД
        # Преобразуем его в строку, чтобы избежать проблем с типами, если БД ожидает текст.
        guild_id_int = int(ctx.guild.id)
        
        for binding in final_bindings_for_upsert:
            # Устанавливаем guild_id для каждой привязки
            binding["guild_id"] = guild_id_int
        logger.debug(f"DEBUG: Добавлен guild_id {guild_id_int} ко всем {len(final_bindings_for_upsert)} привязкам.")
        # 🔥🔥🔥 КОНЕЦ НОВОГО БЛОКА 🔥🔥🔥

        # 🔥🔥🔥 БЛОК ОЧИСТКИ (уже есть у вас, должен идти после добавления guild_id) 🔥🔥🔥
        clean_bindings_for_db_upsert = []
        # Этот список должен содержать ТОЛЬКО те поля, которых НЕТ в вашей модели БД DiscordBinding
        # На данный момент это: "category_name", "channel_name", "description", "parent_access_key"
        # Проверьте, есть ли parent_access_key в вашей модели БД. Если нет - оставьте его здесь.
        fields_to_remove = ["category_name", "channel_name", "description", "parent_access_key"] 
        
        for binding in final_bindings_for_upsert: # Используем final_bindings_for_upsert, который уже содержит guild_id
            clean_binding = binding.copy() # Создаем копию, чтобы не менять исходный словарь
            for field in fields_to_remove:
                if field in clean_binding:
                    del clean_binding[field]
            clean_bindings_for_db_upsert.append(clean_binding)
        
        logger.debug(f"DEBUG: Привязки ПОСЛЕ очистки, отправляемые в БД: {clean_bindings_for_db_upsert}")
        # 🔥🔥🔥 КОНЕЦ БЛОКА ОЧИСТКИ 🔥🔥🔥


        # 7️⃣ **Передаём `clean_bindings_for_db_upsert` в БД**
        logger.info("📌 [ШАГ 7] Запись/обновление привязок категорий и каналов в БД...")
        try:
            # Используем очищенный список для отправки в API
            if clean_bindings_for_db_upsert: 
                api_response = await upsert_discord_bindings_api(clean_bindings_for_db_upsert) 
                
                if api_response and api_response.get("status") == "success":
                    processed_count = api_response.get("processed_count", len(clean_bindings_for_db_upsert))
                    logger.info(f"✅ [ШАГ 7] Успешно записано/обновлено {processed_count} привязок в БД.")
                    await ctx.send("✅ **Структура мира успешно обновлена и сохранена в базе данных!**")
                else:
                    error_message = api_response.get("message", "Неизвестная ошибка API") if api_response else "Пустой или некорректный ответ API."
                    logger.error(f"❌ [ОШИБКА] API вернул неуспешный статус при записи привязок: {error_message}")
                    await ctx.send(f"❌ **Ошибка:** API вернул неуспешный статус при сохранении привязок. Детали: {error_message}")

            else:
                logger.warning("⚠️ [ПРЕДУПРЕЖДЕНИЕ] Нет привязок для сохранения в БД.")
                await ctx.send("⚠️ Создание структуры мира завершено, но нет новых привязок для сохранения.")
        except DiscordAPIClientError as e:
            logger.error(f"❌ [ОШИБКА] Ошибка взаимодействия с Discord API (клиентская): {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Не удалось подключиться к внутреннему API или API вернул ошибку. Детали: {e}")
        except Exception as e:
            logger.error(f"❌ [ОШИБКА] Непредвиденная ошибка при записи привязок в БД: {e}", exc_info=True)
            await ctx.send(f"❌ **Ошибка:** Произошла непредвиденная ошибка при сохранении привязок мира. Детали: {e}")

        logger.info("✅ [КОНЕЦ] Команда `setup_world()` успешно завершена!")


    ### Команда `delete_all_channels` (без изменений)
    @commands.command(name="delete_all_channels", aliases=["DAC"])
    @commands.has_permissions(administrator=True)
    async def delete_all_channels(self, ctx: commands.Context):
        """Удаляет ВСЕ каналы (текстовые, голосовые, категории) на сервере, кроме системного канала."""
        logger.info(f"🔧 [СТАРТ] Команда `delete_all_channels()` запущена пользователем {ctx.author} в гильдии '{ctx.guild.name}' ({ctx.guild.id}).")
        await send_and_delete_temp_message(ctx.channel, "⚠️ **Запущено удаление всех каналов и категорий. Это может занять время.**")

        if not ctx.guild:
            logger.error("❌ [ОШИБКА] `guild` отсутствует! Команда должна быть вызвана в гильдии.")
            await ctx.send("❌ Ошибка: Эта команда должна быть вызвана на сервере Discord!")
            return

        system_channel = ctx.guild.system_channel
        
        channels_to_delete = [
            channel for channel in reversed(ctx.guild.channels) 
            if channel != system_channel 
        ]

        if not channels_to_delete:
            await ctx.send("⚠️ Нет каналов для удаления (кроме системного канала)!")
            logger.info("⚠️ Нет каналов для удаления, процесс завершен.")
            return

        logger.info(f"📌 Найдено {len(channels_to_delete)} каналов и категорий для удаления.")
        delete_count = 0

        for channel in channels_to_delete:
            try:
                await channel.delete()
                logger.info(f"✅ Удалён канал/категория: {channel.name} (ID: {channel.id})")
                delete_count += 1
                await asyncio.sleep(0.5) 
            except discord.Forbidden:
                logger.error(f"❌ Недостаточно прав для удаления канала/категории: {channel.name} (ID: {channel.id}). Проверьте разрешения бота!")
                await ctx.send(f"❌ Не удалось удалить {channel.mention} (`{channel.name}`): у меня недостаточно прав. Убедитесь, что моя роль выше или есть нужные разрешения.")
            except discord.HTTPException as e:
                logger.error(f"❌ Ошибка API при удалении канала/категории {channel.name} (ID: {channel.id}): Статус: {e.status}, Текст: {e.text}", exc_info=True)
                await ctx.send(f"❌ Произошла ошибка Discord API при удалении {channel.mention} (`{channel.name}`). Детали: {e.text}")
            except Exception as e:
                logger.error(f"❌ Непредвиденная ошибка при удалении канала/категории {channel.name} (ID: {channel.id}): {e}", exc_info=True)
                await ctx.send(f"❌ Произошла непредвиденная ошибка при удалении {channel.mention} (`{channel.name}`). Детали: {e}")

        await ctx.send(f"✅ **Удалено {delete_count} каналов и категорий из {len(channels_to_delete)} запланированных!**")
        logger.info(f"🔧 [КОНЕЦ] `delete_all_channels()` завершен. Удалено {delete_count} элементов.")

## Функция Настройки Кога

async def setup(bot):
    """
    Добавляет ког SetupWorldSystem к боту.
    """
    await bot.add_cog(SetupWorldSystem(bot))




