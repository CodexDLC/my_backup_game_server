import os
from discord.ext import commands
from Discord_API.config.logging.logging_setup import logger

class CommandsManager:
    def __init__(self, bot, cogs_directory="cogs"):
        """
        Улучшенный менеджер когов с возможностью перезагрузки
        :param bot: экземпляр бота
        :param cogs_directory: папка с когами
        """
        self.bot = bot
        self.cogs_directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            cogs_directory
        )
        self.EXCLUDED_FOLDERS = ["blueprints", "interface_templates"]
        self.loaded_cogs = set()  # Для отслеживания загруженных когов
        logger.info(f"Инициализирован менеджер когов. Путь: {self.cogs_directory}")

    def _get_cog_path(self, root, filename):
        """Вспомогательный метод для получения пути к когу"""
        relative_path = os.path.relpath(root, self.cogs_directory).replace(os.sep, ".")
        return f"cogs.{relative_path}.{filename[:-3]}" if relative_path != "." else f"cogs.{filename[:-3]}"

    async def load_cogs(self):
        if not os.path.exists(self.cogs_directory):
            logger.error(f"🚨 Папка с когами не найдена: {self.cogs_directory}")
            return False

        success_count = 0
        logger.info(f"🔍 Начинаем сканирование папки: {self.cogs_directory}")

        for root, dirs, files in os.walk(self.cogs_directory):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_FOLDERS]
            logger.debug(f"📂 Проверяем папку: {root}")

            for filename in files:
                if filename.endswith(".py") and filename != "__init__.py":
                    cog_name = self._get_cog_path(root, filename)
                    logger.debug(f"🧐 Найден ког: {cog_name}, пробуем загрузить...")

                    if await self._load_single_cog(cog_name):
                        success_count += 1
                        logger.info(f"✅ Ког загружен успешно: {cog_name}")
                    else:
                        logger.error(f"❌ Ошибка загрузки кога: {cog_name}")

        logger.info(f"🎉 Загрузка завершена: успешно загружено {success_count} когов.")
        return success_count > 0

    async def _load_single_cog(self, cog_name):
        """Загружает один ког с обработкой ошибок"""
        try:
            await self.bot.load_extension(cog_name)
            self.loaded_cogs.add(cog_name)
            logger.info(f"Успешно загружен ког: {cog_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки кога {cog_name}: {type(e).__name__}: {e}")
            return False

    async def reload_cogs(self):
        """Перезагружает все ранее загруженные коги"""
        if not self.loaded_cogs:
            logger.warning("Нет загруженных когов для перезагрузки")
            return False

        success_count = 0
        for cog_name in list(self.loaded_cogs):
            if await self._reload_single_cog(cog_name):
                success_count += 1

        logger.info(f"Перезагрузка завершена. Успешно: {success_count}/{len(self.loaded_cogs)}")
        return success_count == len(self.loaded_cogs)

    async def _reload_single_cog(self, cog_name):
        """Перезагружает один ког с обработкой ошибок"""
        try:
            await self.bot.reload_extension(cog_name)
            logger.info(f"Успешно перезагружен ког: {cog_name}")
            return True
        except Exception as e:
            logger.error(f"Ошибка перезагрузки кога {cog_name}: {type(e).__name__}: {e}")
            self.loaded_cogs.discard(cog_name)  # Удаляем из списка при ошибке
            return False

    async def unload_cogs(self):
        """Выгружает все коги (для перезагрузки или завершения работы)"""
        for cog_name in list(self.loaded_cogs):
            try:
                await self.bot.unload_extension(cog_name)
                self.loaded_cogs.remove(cog_name)
                logger.info(f"Выгружен ког: {cog_name}")
            except Exception as e:
                logger.error(f"Ошибка выгрузки кога {cog_name}: {e}")

async def setup(bot):
    manager = CommandsManager(bot)
    await manager.load_cogs()

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload_command(ctx):
        await manager.unload_cogs()
        if await manager.load_cogs():
            await ctx.send("✅ Все коги успешно перезагружены!")
        else:
            await ctx.send("⚠️ Перезагрузка завершена с ошибками. Проверьте логи.")

    bot.remove_command("reload")
    bot.add_command(reload_command)


