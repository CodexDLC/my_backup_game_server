# game_server/app_discord_bot/app/cogs/system/registration_cog.py
import discord
from discord.ext import commands
import inject
import logging

# Импортируем RegistrationView
from game_server.app_discord_bot.app.ui.views.authentication.registration_view import RegistrationView

# Импортируем тексты
from game_server.app_discord_bot.app.ui.messages.authentication.registration_messages import (
    REGISTRATION_EMBED_TITLE, REGISTRATION_EMBED_DESCRIPTION, 
    REGISTRATION_EMBED_FOOTER, COMMAND_RESPONSES
    )

# Импортируем константу канала регистрации (если используется по умолчанию)
from game_server.app_discord_bot.app.constant.constants_world import REGISTRATION_CHANNEL_ID

# Импортируем GuildConfigManager и RedisKeys для сохранения message_id
from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys


class RegistrationCog(commands.Cog):
    """
    Ког, управляющий UI-компонентами регистрации.
    Отвечает за отправку сообщения с кнопками регистрации и его перепривязку.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger, guild_config_manager: GuildConfigManager):
        self.bot = bot
        self.logger = logger
        self.guild_config_manager = guild_config_manager # Инжектируем GuildConfigManager
        self.logger.info("✨ RegistrationCog инициализирован.")

    @commands.command(name="send_registration_message")
    @commands.has_permissions(administrator=True) # Только администраторы могут использовать эту команду
    async def send_registration_message(self, ctx: commands.Context, channel_id: int = None):
        """
        Отправляет сообщение с кнопками регистрации в указанный канал.
        Если channel_id не указан, будет использован REGISTRATION_CHANNEL_ID из констант.
        Команда будет удалена через минуту.
        Использование: !send_registration_message [ID_канала]
        """
        # 🔥 НОВОЕ: Откладываем ответ на команду, чтобы избежать таймаута
        # ephemeral=True делает ответ видимым только для пользователя
        # thinking=True показывает "Бот думает..."
        await ctx.defer(ephemeral=True, thinking=True)


        target_channel_id = channel_id if channel_id is not None else REGISTRATION_CHANNEL_ID
        
        try:
            target_channel = self.bot.get_channel(target_channel_id)
            if not target_channel:
                # 🔥 ИСПРАВЛЕНИЕ: Используем followup.send, так как ctx.defer() уже был вызван
                await ctx.followup.send(
                    COMMAND_RESPONSES["channel_not_found"].format(target_channel_id),
                    ephemeral=True, delete_after=60
                )
                return

            embed = discord.Embed(
                title=REGISTRATION_EMBED_TITLE,
                description=REGISTRATION_EMBED_DESCRIPTION,
                color=discord.Color.blue()
            )
            embed.set_footer(text=REGISTRATION_EMBED_FOOTER)

            # Отправляем сообщение с нашим постоянным View
            message = await target_channel.send(embed=embed, view=RegistrationView(self.bot))
            
            # --- Сохраняем ID сообщения в Redis ---
            # Предполагаем, что guild_id Хаба - это ctx.guild.id
            hub_guild_id = ctx.guild.id 
            await self.guild_config_manager.set_field(
                guild_id=hub_guild_id,
                shard_type="hub", # Тип шарда "hub"
                field_name=RedisKeys.FIELD_REGISTRATION_MESSAGE_ID, # Используем константу из RedisKeys
                data=str(message.id) # Сохраняем ID сообщения как строку
            )
            self.logger.success(f"ID сообщения регистрации ({message.id}) сохранен в Redis для хаба {hub_guild_id}.")

            # 🔥 ИСПРАВЛЕНИЕ: Используем followup.send для финального ответа
            await ctx.followup.send(
                COMMAND_RESPONSES["success_sent"].format(target_channel_id),
                ephemeral=True, delete_after=60
            )
            self.logger.info(f"Сообщение регистрации отправлено в канал {target_channel_id} по команде администратора {ctx.author.id}.")

        except Exception as e:
            self.logger.error(f"Ошибка при отправке сообщения регистрации: {e}", exc_info=True)
            # 🔥 ИСПРАВЛЕНИЕ: Используем followup.send для ответа об ошибке
            # Проверяем, не был ли ответ уже отправлен (хотя ctx.defer() делает это менее вероятным)
            if not ctx.interaction.response.is_done():
                 await ctx.followup.send(
                    COMMAND_RESPONSES["error_sending"].format(e),
                    ephemeral=True, delete_after=60
                )
        finally:
            # Удаляем сообщение команды администратора через 60 секунд
            # ctx.message доступно только до того, как ctx.defer/respond вызван
            # Если команда была слеш-командой, ctx.message может быть None
            if ctx.message: # Проверяем, что это не слеш-команда и message существует
                await ctx.message.delete(delay=60)

# Функция setup для загрузки кога
async def setup(bot: commands.Bot):
    # inject автоматически разрешит logger и guild_config_manager
    await bot.add_cog(inject.call(RegistrationCog, bot=bot)) # Инжектируем cog