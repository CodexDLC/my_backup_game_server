from .test_config import LOGIC_HANDLER_MAP, PRESENTATION_HANDLER_MAP
from . import test_helpers

class TestExampleOrchestrator:
    """
    Оркестратор для тестового сервиса.
    """
    async def process(self, command_str: str, interaction):
        print(f"[+] Оркестратор test_example получил команду: '{command_str}'")
        
        # 1. Вызов обработчика логики
        command_parts = command_str.split(':', 1)
        command_name = command_parts[0]
        payload = command_parts[1] if len(command_parts) > 1 else None
        
        LogicHandler = LOGIC_HANDLER_MAP.get(command_name)
        if not LogicHandler:
            print(f"[!] Обработчик логики для команды '{command_name}' не найден.")
            return

        logic_handler_instance = LogicHandler()
        data = await logic_handler_instance.execute(payload, interaction)
        
        # 2. Вызов обработчика представления
        data_type = data.get("type")
        PresentationHandler = PRESENTATION_HANDLER_MAP.get(data_type)
        if not PresentationHandler:
            print(f"[!] Обработчик представления для типа '{data_type}' не найден.")
            return

        presentation_handler_instance = PresentationHandler()
        await presentation_handler_instance.execute(data, interaction, test_helpers)