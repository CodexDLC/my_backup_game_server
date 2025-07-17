# game_server/app_discord_bot/app/services/utils/message_sender_service.py
import discord
import logging
import inject
from typing import Dict, Any, Optional, Type # Добавлено Type для type hinting ViewClass

# Импорты для работы с Redis

from game_server.app_discord_bot.storage.cache.managers.guild_config_manager import GuildConfigManager


class MessageSenderService:
    """
    Сервис, отвечающий за отправку, редактирование и удаление сообщений Discord
    с Embed и View, а также за сохранение их ID для перепривязки постоянных View.
    """
    @inject.autoparams()
    def __init__(
        self,
        guild_config_manager: GuildConfigManager,
        logger: logging.Logger
    ):
        self.guild_config_manager = guild_config_manager
        self.logger = logger
        self.logger.info("✨ MessageSenderService инициализирован.")

    async def send_message_with_view(
        self,
        guild: discord.Guild,
        channel_id: int, # ID канала для отправки
        embed_title: str,
        embed_description: str,
        embed_footer: str,
        view_class: Type[discord.ui.View], # Принимаем КЛАСС View
        bot_instance: discord.Client, # Передаем bot_instance, если View его ожидает в конструкторе
        redis_field_name: Optional[str] = None, # Для сохранения ID сообщения, если View постоянный
        shard_type: str = "game", # Тип шарда для Redis, по умолчанию "game"
        embed_color: discord.Color = discord.Color.green(), # Цвет Embed
        
    ) -> Optional[discord.Message]:
        """
        Универсальный метод для отправки нового сообщения с Embed и постоянным View в указанный канал.
        Сохраняет ID сообщения в Redis, если указан redis_field_name.
        """
        self.logger.info(f"Попытка отправить универсальное сообщение в канал {channel_id} для гильдии {guild.id}.") 

        target_channel = guild.get_channel(channel_id)
        if not target_channel:
            self.logger.error(f"Канал с ID {channel_id} не найден на гильдии {guild.id}. Сообщение не будет отправлено.")
            return None
        
        if not isinstance(target_channel, (discord.TextChannel, discord.Thread)): # Позволяем отправлять и в треды
            self.logger.error(f"Канал с ID {channel_id} на гильдии {guild.id} не является текстовым каналом или тредом. Сообщение не будет отправлено.")
            return None

        try:
            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=embed_color
            )
            embed.set_footer(text=embed_footer)

            # Создаем экземпляр View, передавая bot_instance, как это делает RegistrationView/LoginView
            view_instance = view_class(bot_instance=bot_instance) 
            
            message = await target_channel.send(embed=embed, view=view_instance) # 🔥 ИСПРАВЛЕНИЕ: Удален аргумент ephemeral
            
            if message:
                if redis_field_name:
                    await self.guild_config_manager.set_field(
                        guild_id=guild.id,
                        shard_type=shard_type,
                        field_name=redis_field_name,
                        data=str(message.id)
                    )
                    self.logger.success(f"ID сообщения ({message.id}) для '{redis_field_name}' сохранено в Redis для гильдии {guild.id}.")
                self.logger.success(f"Универсальное сообщение успешно отправлено в канал {target_channel.name} ({target_channel.id}) на гильгии {guild.id}.")
                return message
            else:
                self.logger.warning(f"channel.send() вернул None для канала {target_channel.name} ({target_channel.id}). Сообщение, возможно, не было отправлено.")
                return None

        except discord.Forbidden:
            self.logger.error(f"У бота нет прав для отправки сообщений в канал {target_channel.name} ({target_channel.id}) на гильдии {guild.id}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при отправке универсального сообщения в канал {target_channel.name} ({target_channel.id}) на гильдии {guild.id}: {e}", exc_info=True)
            return None

    async def edit_message_with_view(
        self,
        guild: discord.Guild,
        channel_id: int,
        message_id: int, # ID сообщения, которое нужно отредактировать
        embed_title: str,
        embed_description: str,
        embed_footer: str,
        view_class: Type[discord.ui.View],
        bot_instance: discord.Client,
        embed_color: discord.Color = discord.Color.green()
    ) -> Optional[discord.Message]:
        """
        Редактирует существующее сообщение с новым Embed и View в указанном канале.
        """
        self.logger.info(f"Попытка редактировать сообщение {message_id} в канале {channel_id} на гильдии {guild.id}.")

        target_channel = guild.get_channel(channel_id)
        if not target_channel:
            self.logger.error(f"Канал с ID {channel_id} не найден на гильдии {guild.id} для редактирования сообщения {message_id}.")
            return None
        
        if not isinstance(target_channel, (discord.TextChannel, discord.Thread)):
            self.logger.error(f"Канал с ID {channel_id} на гильдии {guild.id} не является текстовым каналом или тредом. Невозможно редактировать сообщение {message_id}.")
            return None

        try:
            # Получаем объект сообщения
            message_to_edit = await target_channel.fetch_message(message_id)

            if not message_to_edit:
                self.logger.error(f"Сообщение с ID {message_id} не найдено в канале {channel_id} для редактирования.")
                return None

            embed = discord.Embed(
                title=embed_title,
                description=embed_description,
                color=embed_color
            )
            embed.set_footer(text=embed_footer)

            # Создаем экземпляр View, как и для отправки нового сообщения
            view_instance = view_class(bot_instance=bot_instance) 
            
            edited_message = await message_to_edit.edit(embed=embed, view=view_instance)
            
            if edited_message:
                self.logger.success(f"Сообщение {message_id} успешно отредактировано в канале {target_channel.name} ({target_channel.id}) на гильдии {guild.id}.")
                return edited_message
            else:
                self.logger.warning(f"message.edit() вернул None для сообщения {message_id}. Сообщение, возможно, не было отредактировано.")
                return None

        except discord.NotFound:
            self.logger.error(f"Сообщение с ID {message_id} не найдено в канале {channel_id} (или было удалено).", exc_info=True)
            return None
        except discord.Forbidden:
            self.logger.error(f"У бота нет прав для редактирования сообщения {message_id} в канале {channel_id} на гильдии {guild.id}.", exc_info=True)
            return None
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при редактировании сообщения {message_id} в канале {channel_id} на гильдии {guild.id}: {e}", exc_info=True)
            return None

    async def delete_message(
        self,
        guild: discord.Guild,
        channel_id: int,
        message_id: int
    ) -> bool:
        """
        Удаляет сообщение из указанного канала.
        """
        self.logger.info(f"Попытка удалить сообщение {message_id} из канала {channel_id} на гильдии {guild.id}.")

        target_channel = guild.get_channel(channel_id)
        if not target_channel:
            self.logger.error(f"Канал с ID {channel_id} не найден на гильдии {guild.id} для удаления сообщения {message_id}.")
            return False
        
        if not isinstance(target_channel, (discord.TextChannel, discord.Thread)):
            self.logger.error(f"Канал с ID {channel_id} на гильдии {guild.id} не является текстовым каналом или тредом. Невозможно удалить сообщение {message_id}.")
            return False

        try:
            message_to_delete = await target_channel.fetch_message(message_id)
            if message_to_delete:
                await message_to_delete.delete()
                self.logger.success(f"Сообщение {message_id} успешно удалено из канала {target_channel.name} ({target_channel.id}) на гильдии {guild.id}.")
                return True
            else:
                self.logger.warning(f"Сообщение с ID {message_id} не найдено в канале {channel_id} для удаления.")
                return False

        except discord.NotFound:
            self.logger.warning(f"Сообщение с ID {message_id} не найдено в канале {channel_id} (возможно, уже удалено).", exc_info=True)
            return True # Считаем успехом, если сообщения уже нет
        except discord.Forbidden:
            self.logger.error(f"У бота нет прав для удаления сообщения {message_id} в канале {channel_id} на гильдии {guild.id}.", exc_info=True)
            return False
        except Exception as e:
            self.logger.critical(f"Критическая ошибка при удалении сообщения {message_id} из канала {channel_id} на гильдии {guild.id}: {e}", exc_info=True)
            return False
    
