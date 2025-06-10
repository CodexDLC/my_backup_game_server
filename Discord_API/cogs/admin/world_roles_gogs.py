import asyncio
import discord
from discord.ext import commands
from Discord_API.api_route_function.spec_route.state_entities_discord_api import create_roles_discord
from Discord_API.discord_functions.utils.world_setup_gogs.setup_roles_utils import build_roles_batch, find_missing_roles, send_and_delete_temp_message
from Discord_API.discord_functions.world_setup import create_discord_roles
from Discord_API.config.logging.logging_setup import logger





class SetupRolesSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Создаем асинхронный замок для предотвращения параллельного выполнения операций синхронизации
        self._sync_operation_lock = asyncio.Lock() 
        logger.info("SetupRolesSystem инициализирован.")

    # --- `setup_roles` Command ---
    @commands.command(name="setup_roles", aliases=["SR"])
    @commands.has_permissions(administrator=True)
    async def setup_roles(self, ctx: commands.Context):
        """Запускает процесс создания и синхронизации ролей в Discord на основе данных мира."""

        # ❗ ПРОВЕРКА ЗАМКА ❗
        if self._sync_operation_lock.locked():
            await ctx.send("❗ Другая операция синхронизации ролей уже выполняется. Пожалуйста, подождите ее завершения.")
            logger.warning(f"Попытка запустить `setup_roles`, пока lock занят. Пользователь: {ctx.author} в гильдии: {ctx.guild.name}")
            return

        async with self._sync_operation_lock: # Захватываем замок на время выполнения команды
            logger.info(f"🔧 [START] Команда `setup_roles()` запущена пользователем {ctx.author} в гильдии '{ctx.guild.name}' ({ctx.guild.id}).")

            guild_id = ctx.guild.id if ctx.guild else None
            if guild_id is None:
                logger.error("❌ [ERROR] `guild_id` отсутствует! Команда должна быть вызвана в гильдии.")
                await ctx.send("❌ Ошибка: Эта команда должна быть вызвана на сервере Discord!")
                return

            # 📌 1️⃣ Определяем недостающие роли
            logger.info(f"🔍 [STEP 1] Запрашиваем `find_missing_roles()` для гильдии {guild_id}...")
            try:
                missing_roles = await find_missing_roles(guild_id)
            except Exception as e:
                logger.error(f"❌ [ERROR] Ошибка при определении недостающих ролей в БД: {e}", exc_info=True)
                await ctx.send(f"❌ Произошла ошибка при определении ролей для синхронизации. Попробуйте позже. Детали: {e}")
                return

            if not missing_roles:
                logger.warning("⚠️ [WARN] Нет новых ролей для создания или синхронизации.")
                await ctx.send("⚠️ Все необходимые роли уже синхронизированы в базе данных. Новых ролей для создания нет.")
                logger.info("🔧 [END] `setup_roles()` завершен без изменений.")
                return # Замок будет освобожден при выходе из async with

            # 🔥 2️⃣ Создаем/обновляем роли в Discord
            logger.info(f"🔧 [STEP 2] Запуск `create_discord_roles()` для {len(missing_roles)} ролей.")
            await send_and_delete_temp_message(
                ctx.channel, # Отправляем сообщение в канал, где была вызвана команда
                f"⏳ Начинаю синхронизацию {len(missing_roles)} ролей. Это может занять некоторое время."
            )
            try:
                roles_bindings = await create_discord_roles(ctx.guild, missing_roles)
                logger.info(f"✅ [STEP 2] `create_discord_roles()` успешно завершен. Обработано {len(roles_bindings)} привязок.")
            except discord.Forbidden:
                logger.error(f"❌ [ERROR] Боту не хватает прав для создания/управления ролями в гильдии '{ctx.guild.name}'.")
                await ctx.send("❌ Ошибка прав: У меня недостаточно разрешений для создания или изменения ролей. Проверьте мои разрешения.")
                return # Замок будет освобожден при выходе из async with
            except discord.HTTPException as e:
                logger.error(f"❌ [ERROR] Ошибка API Discord при создании/обновлении ролей (статус: {e.status}, текст: {e.text}): {e}", exc_info=True)
                await ctx.send(f"❌ Произошла ошибка связи с Discord API при синхронизации ролей. Попробуйте позже. Детали: {e.text}")
                return # Замок будет освобожден при выходе из async with
            except Exception as e:
                logger.error(f"❌ [ERROR] Непредвиденная ошибка при создании/обновлении ролей: {e}", exc_info=True)
                await ctx.send(f"❌ Произошла непредвиденная ошибка при синхронизации ролей. Детали: {e}")
                return # Замок будет освобожден при выходе из async with

            if not roles_bindings:
                logger.warning("⚠️ [WARN] `create_discord_roles` не вернул никаких привязок. Возможно, все роли уже существовали, но не были синхронизированы.")
                await ctx.send("⚠️ Синхронизация ролей завершена, но не удалось получить привязки. Проверьте логи.")
                return # Замок будет освобожден при выходе из async with

            # 📌 3️⃣ Формируем `roles_batch` перед записью в БД
            logger.info(f"🔍 [STEP 3] Формируем `roles_batch` из {len(roles_bindings)} привязок...")
            try:
                roles_batch = await build_roles_batch(roles_bindings)
                logger.info(f"✅ [STEP 3] `roles_batch` успешно сформирован ({len(roles_batch)} элементов).")
            except Exception as e:
                logger.error(f"❌ [ERROR] Ошибка при формировании `roles_batch`: {e}", exc_info=True)
                await ctx.send(f"❌ Ошибка при подготовке данных для сохранения ролей в базу данных. Детали: {e}")
                return # Замок будет освобожден при выходе из async with

            # 📌 4️⃣ Сохраняем роли в БД
            logger.info(f"🔍 [STEP 4] Запись {len(roles_batch)} привязок ролей в БД...")
            try:
                await create_roles_discord(roles_batch) # Убедитесь, что эта функция выполняет UPSERT (вставка/обновление)
                logger.info("✅ [STEP 4] Роли успешно сохранены в БД.")
                await ctx.send("✅ Все роли успешно синхронизированы и сохранены в базе данных!")
            except Exception as e:
                logger.error(f"❌ [ERROR] Ошибка при записи ролей в БД: {e}", exc_info=True)
                await ctx.send(f"❌ Ошибка при сохранении ролей в базу данных. Детали: {e}")
            
            logger.info("🔧 [END] Команда `setup_roles()` успешно завершена!")
        # Замок автоматически освобождается при выходе из блока `async with`

    # --- `purge_roles` Command ---
    @commands.command(name="purge_roles", aliases=["pr"])
    @commands.has_permissions(administrator=True)
    async def purge_roles(self, ctx: commands.Context):
        """Удаляет все роли в гильдии, кроме роли бота."""

        # ❗ ПРОВЕРКА ЗАМКА ❗
        if self._sync_operation_lock.locked():
            await ctx.send("❗ Другая операция синхронизации ролей уже выполняется. Пожалуйста, подождите ее завершения.")
            logger.warning(f"Попытка запустить `purge_roles`, пока lock занят. Пользователь: {ctx.author} в гильдии: {ctx.guild.name}")
            return

        async with self._sync_operation_lock: # Захватываем замок
            logger.info(f"🔧 [START] Команда `purge_roles()` запущена пользователем {ctx.author} в гильдии '{ctx.guild.name}' ({ctx.guild.id}).")
            await ctx.send("🔧 **Начинаем удаление ролей...**")

            if not ctx.guild:
                logger.error("❌ [ERROR] `guild` отсутствует! Команда должна быть вызвана в гильдии.")
                await ctx.send("❌ Ошибка: Эта команда должна быть вызвана на сервере Discord!")
                return # Замок будет освобожден при выходе из async with

            bot_role = ctx.guild.me.top_role
            # Filter out the @everyone role and the bot's own role
            roles_to_delete = [role for role in ctx.guild.roles if role.id != ctx.guild.id and role != bot_role]

            if not roles_to_delete:
                await ctx.send("⚠️ Нет ролей для удаления (кроме @everyone и роли бота)!")
                logger.info("⚠️ Нет ролей для удаления, процесс завершен.")
                return # Замок будет освобожден при выходе из async with

            logger.info(f"📌 Найдено {len(roles_to_delete)} ролей для удаления.")
            delete_count = 0

            for role in roles_to_delete:
                try:
                    await role.delete()
                    logger.info(f"✅ Удалена роль: {role.name} (ID: {role.id})")
                    delete_count += 1
                    # Optional: Add a small delay to avoid hitting rate limits if many roles
                    await asyncio.sleep(0.5) 
                except discord.Forbidden:
                    logger.error(f"❌ Недостаточно прав для удаления роли: {role.name} (ID: {role.id}). Проверьте иерархию ролей бота!")
                    await ctx.send(f"❌ Не удалось удалить роль **{role.name}**: у меня недостаточно прав. Убедитесь, что моя роль выше удаляемой.")
                except discord.HTTPException as e:
                    logger.error(f"❌ Ошибка API при удалении роли {role.name} (ID: {role.id}): Статус: {e.status}, Текст: {e.text}", exc_info=True)
                    await ctx.send(f"❌ Произошла ошибка Discord API при удалении роли **{role.name}**. Детали: {e.text}")
                except Exception as e:
                    logger.error(f"❌ Непредвиденная ошибка при удалении роли {role.name} (ID: {role.id}): {e}", exc_info=True)
                    await ctx.send(f"❌ Произошла непредвиденная ошибка при удалении роли **{role.name}**. Детали: {e}")

            await ctx.send(f"✅ **Удалено {delete_count} ролей из {len(roles_to_delete)} запланированных (кроме @everyone и роли бота)!**")
            logger.info(f"🔧 [END] `purge_roles()` завершен. Удалено {delete_count} ролей.")
        # Замок автоматически освобождается при выходе из блока `async with`

## Cog Setup Function

async def setup(bot):
    """
    Добавляет ког SetupRolesSystem к боту.
    """
    await bot.add_cog(SetupRolesSystem(bot))