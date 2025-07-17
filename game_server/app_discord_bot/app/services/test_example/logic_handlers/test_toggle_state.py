class TestToggleStateHandler:
    """
    Обработчик-переключатель. На основе текущего состояния
    возвращает данные для следующего состояния.
    """
    async def execute(self, target_state: str, interaction):
        print(f"[+] Logic Handler: Переключаемся в состояние '{target_state}'")
        
        if target_state == "A":
            # Данные для построения зеленого сообщения
            return {
                "type": "toggle_message", 
                "text": "Состояние А (зеленое)",
                "next_state": "A"
            }
        else: # target_state == "B"
            # Данные для построения красного сообщения
            return {
                "type": "toggle_message", 
                "text": "Состояние Б (красное)",
                "next_state": "B"
            }