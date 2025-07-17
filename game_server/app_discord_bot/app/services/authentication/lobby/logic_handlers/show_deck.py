# game_server\app_discord_bot\app\services\authentication\lobby\logic_handlers\show_deck.py



from game_server.app_discord_bot.core.contracts.handler_response_dto import StubResponseDTO


class ShowDeckHandler:
    """Обработчик-заглушка для команды 'Колода'."""
    async def execute(self, payload: str, interaction):
        print(f"[+] Logic Handler (show_deck): Заглушка вызвана.")
        return StubResponseDTO(
            type="deck_view_stub",
            message="Управление колодой находится в разработке."
        )