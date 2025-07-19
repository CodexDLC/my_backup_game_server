import discord
import inject

class ShowFaqHandler:
    """
    Простой обработчик для команды 'show_faq'.
    Отправляет сообщение-заглушку о том, что раздел в разработке.
    """
    @inject.autoparams()
    def __init__(self):
        # Сейчас зависимостей нет, но в будущем здесь может быть,
        # например, сервис для получения текста из базы данных.
        pass

    async def execute(self, payload: str | None, interaction: discord.Interaction, **kwargs) -> None:
        """
        Отправляет эфемерное сообщение и возвращает None, чтобы остановить цепочку.
        """
        # ▼▼▼ ЭТОТ ТЕКСТ ВЫ СМОЖЕТЕ ЛЕГКО ИЗМЕНИТЬ В БУДУЩЕМ ▼▼▼
        placeholder_text = "Раздел FAQ находится в разработке. Скоро здесь появится полезная информация."

        # Проверяем, был ли уже дан ответ на взаимодействие
        if not interaction.response.is_done():
            await interaction.response.send_message(placeholder_text, ephemeral=True)
        else:
            await interaction.followup.send(placeholder_text, ephemeral=True)
        
        # Возвращаем None, чтобы оркестратор понял, что работа завершена
        return None