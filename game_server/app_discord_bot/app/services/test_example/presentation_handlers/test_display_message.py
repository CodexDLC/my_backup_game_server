# Импортируем оба наших View


from game_server.app_discord_bot.app.ui.views.admin.test_green_view import TestGreenView
from game_server.app_discord_bot.app.ui.views.admin.test_red_view import TestRedView


class TestDisplayToggleMessageHandler:
    """
    Обработчик представления. Выбирает нужный View и редактирует сообщение.
    """
    async def execute(self, data: dict, interaction, helpers):
        print(f"[+] Presentation Handler: Отображаем состояние '{data.get('next_state')}'")
        
        text_content = data.get("text")
        next_state = data.get("next_state")
        
        # Выбираем, какой View прикрепить к сообщению
        if next_state == "A":
            view_to_show = TestGreenView()
        else:
            view_to_show = TestRedView()
            
        # Используем хелпер для РЕДАКТИРОВАНИЯ исходного сообщения
        await helpers.edit_message(interaction, new_text=text_content, new_view=view_to_show)