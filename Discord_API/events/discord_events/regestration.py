import discord
from discord.ext import commands
from Discord_API.ui_templates.register_button import StartButton
from Discord_API.config.logging.logging_setup import logger

class RegistrationCog(commands.Cog):
    """Ког для регистрации пользователей через текстовый канал"""

    def __init__(self, bot):
        self.bot = bot
        self.reg_channel_id = 1368550108240805968  # ID текстового канала "регистрация"
        self.sent_users = set()

        logger.info(f"✅ RegistrationCog инициализирован, отслеживание канала {self.reg_channel_id}")

    async def send_welcome(self, user):
        """Отправляет приветственное сообщение с кнопкой"""
        try:
            view = StartButton()
            await user.send(
                "🎮 **Добро пожаловать!**\n"
                "Нажмите кнопку ниже для регистрации:",
                view=view
            )
            logger.info(f"✅ Успешно отправлено приветственное сообщение {user.name}")
            return True
        except discord.Forbidden:
            logger.warning(f"⚠️ Не удалось отправить ЛС {user.name}, возможно, закрыты личные сообщения")
            return False

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Реагирует на вход в текстовый канал 'регистрация'"""
        guild = after.guild
        target_channel = discord.utils.get(guild.channels, id=self.reg_channel_id)

        if target_channel and after in target_channel.members and after.id not in self.sent_users:
            logger.info(f"👀 Пользователь {after.name} вошел в канал регистрации {target_channel.name}")

            if not await self.send_welcome(after):
                logger.warning(f"⚠️ {after.name} не смог получить ЛС, отправляем сообщение в канал!")
                await target_channel.send(
                    f"{after.mention}, пожалуйста, включите ЛС для регистрации!",
                    delete_after=60
                )

            self.sent_users.add(after.id)
            logger.info(f"✅ Пользователь {after.name} добавлен в список обработанных")

async def setup(bot):
    await bot.add_cog(RegistrationCog(bot))
    logger.info("✅ RegistrationCog загружен и готов к работе")
