# game_server/app_discord_bot/app/ui/views/inspection/components.py

import discord
from typing import List, Optional, Dict, Any

# Импортируем наши DTO
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_dtos import InspectedEntityDTO

# --- Классы кнопок действий (для 2-го и 3-го уровней) ---
# ViewDetailsActionButton - для 2-го уровня
# Остальные - для 3-го уровня

class ViewDetailsActionButton(discord.ui.Button):
    """Кнопка 'Взаимодействовать' для сущности (общий осмотр/детали). Используется на 2-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Взаимодействовать", style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs) 

class InspectActionButton(discord.ui.Button):
    """Кнопка 'Осмотреть' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Осмотреть", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

class InteractActionButton(discord.ui.Button):
    """Кнопка 'Взаимодействовать' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Взаимодействовать", style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs)

class AttackActionButton(discord.ui.Button):
    """Кнопка 'Атаковать' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Атаковать", style=discord.ButtonStyle.danger, custom_id=custom_id, **kwargs)

class TradeActionButton(discord.ui.Button):
    """Кнопка 'Торговать' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Торговать", style=discord.ButtonStyle.green, custom_id=custom_id, **kwargs)

class ProfileActionButton(discord.ui.Button):
    """Кнопка 'Профиль' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Профиль", style=discord.ButtonStyle.blurple, custom_id=custom_id, **kwargs)

class MessageActionButton(discord.ui.Button):
    """Кнопка 'Сообщение' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Сообщение", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

# AddFriendActionButton УДАЛЕН, так как будет создаваться динамически
# class AddFriendActionButton(discord.ui.Button):
#     """Кнопка 'Добавить в друзья' для сущности. Используется на 3-м уровне."""
#     def __init__(self, custom_id: str, **kwargs):
#         super().__init__(style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs)

class QuestActionButton(discord.ui.Button):
    """Кнопка 'Задание' для сущности. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Задание", style=discord.ButtonStyle.success, custom_id=custom_id, **kwargs)

class OpenChestActionButton(discord.ui.Button):
    """Кнопка 'Открыть' для сундука. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Открыть", style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs)

class InspectChestActionButton(discord.ui.Button):
    """Кнопка 'Осмотреть' для сундука. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Осмотреть", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

class JoinBattleActionButton(discord.ui.Button):
    """Кнопка 'Присоединиться' к бою. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Присоединиться", style=discord.ButtonStyle.danger, custom_id=custom_id, **kwargs)

class ObserveBattleActionButton(discord.ui.Button):
    """Кнопка 'Наблюдать' за боем. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Наблюдать", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

class EnterPortalActionButton(discord.ui.Button):
    """Кнопка 'Войти' в портал. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Войти", style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs)

class InspectPortalActionButton(discord.ui.Button):
    """Кнопка 'Осмотреть' портал. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Осмотреть", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

class InspectMerchantActionButton(discord.ui.Button):
    """Кнопка 'Осмотреть' торговца. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Осмотреть", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)

class CraftActionButton(discord.ui.Button):
    """Кнопка 'Использовать' (крафт) для станции. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Использовать", style=discord.ButtonStyle.primary, custom_id=custom_id, **kwargs)

class InspectStationActionButton(discord.ui.Button):
    """Кнопка 'Осмотреть' станцию крафта. Используется на 3-м уровне."""
    def __init__(self, custom_id: str, **kwargs):
        super().__init__(label="Осмотреть", style=discord.ButtonStyle.secondary, custom_id=custom_id, **kwargs)


# --- EntitySelect (без изменений) ---

class EntitySelect(discord.ui.Select):
    """Локальный компонент: выпадающий список для выбора сущности."""
    def __init__(self, entities: List[InspectedEntityDTO], current_category_key: str):
        options = [
            discord.SelectOption(label=entity.label, description=entity.description, value=entity.entity_id)
            for entity in entities
        ]
        if not options:
            options.append(discord.SelectOption(label="В этой категории пусто", value="placeholder", default=True))
            
        super().__init__(
            placeholder="Выберите объект для детального осмотра...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.current_category_key = current_category_key # Сохраняем category_key для использования в callback

    async def callback(self, interaction: discord.Interaction):
        selected_entity_id = self.values[0]
        
        # Вызываем метод родительского View для обработки выбора и активации кнопок
        if hasattr(self.view, 'on_entity_selected') and callable(getattr(self.view, 'on_entity_selected')):
            await self.view.on_entity_selected(interaction, selected_entity_id, self.current_category_key)
        else:
            await interaction.response.send_message(
                f"Вы выбрали объект с ID: {selected_entity_id}. Логика активации кнопок не найдена.",
                ephemeral=True
            )

