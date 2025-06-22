import discord

# =================================================================================
# --- 1. УНИВЕРСАЛЬНЫЕ КНОПКИ (ДЛЯ ОБЩИХ ДЕЙСТВИЙ) ---
# =================================================================================

class BackButton(discord.ui.Button):
    """Универсальная кнопка "Назад" (серая). Делегирует действие методу on_back."""
    def __init__(self, row: int = 4):
        super().__init__(label="Назад", emoji="⬅️", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_back'):
            await self.view.on_back(interaction)

class ConfirmButton(discord.ui.Button):
    """Универсальная кнопка "Подтвердить" (зеленая). Делегирует действие методу on_confirm."""
    def __init__(self, label: str = "Подтвердить", row: int = 4):
        super().__init__(label=label, emoji="✔️", style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_confirm'):
            await self.view.on_confirm(interaction)

class CancelButton(discord.ui.Button):
    """Универсальная кнопка "Отмена" или "Закрыть" (серая). Делегирует действие методу on_cancel."""
    def __init__(self, label: str = "Отмена", row: int = 4):
        super().__init__(label=label, emoji="❌", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_cancel'):
            await self.view.on_cancel(interaction)

class DeleteButton(discord.ui.Button):
    """Универсальная кнопка для опасного действия "Удалить" (красная). Делегирует действие методу on_delete."""
    def __init__(self, label: str = "Удалить", row: int = 4):
        super().__init__(label=label, emoji="🔥", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_delete'):
            await self.view.on_delete(interaction)

# =================================================================================
# --- 2. КНОПКИ ДЛЯ ПРОЦЕССА ВХОДА И ЛОББИ ---
# =================================================================================

class LoginButton(discord.ui.Button):
    """Кнопка для начала сессии "Войти в игру" (синяя). Делегирует действие методу on_login."""
    def __init__(self, row: int = 0):
        super().__init__(label="Войти в игру", emoji="▶️", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_login'):
            await self.view.on_login(interaction)

class CharactersButton(discord.ui.Button):
    """Кнопка для перехода к выбору персонажа "Персонажи" (синяя). Делегирует действие методу on_characters."""
    def __init__(self, row: int = 0):
        super().__init__(label="Персонажи", emoji="👥", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_characters'):
            await self.view.on_characters(interaction)

class DeckButton(discord.ui.Button):
    """Кнопка для меню "Колода" (серая, неактивная)."""
    def __init__(self, row: int = 0):
        super().__init__(label="Колода", emoji="🃏", style=discord.ButtonStyle.secondary, row=row, disabled=True)
    
    # Callback не нужен, так как кнопка неактивна
    # async def callback(self, interaction: discord.Interaction): pass

class EnterWorldButton(discord.ui.Button):
    """Кнопка для подтверждения выбора персонажа "Войти в мир" (зеленая). Делегирует действие методу on_enter_world."""
    def __init__(self, row: int = 1):
        super().__init__(label="Войти в мир", emoji="✅", style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_enter_world'):
            await self.view.on_enter_world(interaction)

class CreateCharacterButton(discord.ui.Button):
    """
    Кнопка для запуска процесса создания нового персонажа (зеленая).
    Делегирует действие методу on_create_character.
    """
    def __init__(self, row: int = 0):
        super().__init__(
            label="Создать персонажа", 
            emoji="➕", 
            style=discord.ButtonStyle.success, 
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_create_character'):
            await self.view.on_create_character(interaction)
        else:
            # Это сообщение можно будет убрать, когда реализуем логику
            await interaction.response.send_message("Процесс создания персонажа в разработке.", ephemeral=True)

# =================================================================================
# --- 3. КНОПКИ ДЛЯ ОСНОВНОЙ ПАНЕЛИ УПРАВЛЕНИЯ ---
# =================================================================================

class ProfileButton(discord.ui.Button):
    """Кнопка для вызова меню "Профиль" (синяя). Делегирует действие методу on_profile."""
    def __init__(self, row: int = 0):
        super().__init__(label="Профиль", emoji="👤", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_profile'):
            await self.view.on_profile(interaction)

class InventoryButton(discord.ui.Button):
    """Кнопка для вызова "Инвентаря" (синяя). Делегирует действие методу on_inventory."""
    def __init__(self, row: int = 0):
        super().__init__(label="Инвентарь", emoji="🎒", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_inventory'):
            await self.view.on_inventory(interaction)

class SkillsButton(discord.ui.Button):
    """Кнопка для вызова меню "Навыки" (синяя). Делегирует действие методу on_skills."""
    def __init__(self, row: int = 0):
        super().__init__(label="Навыки", emoji="✨", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_skills'):
            await self.view.on_skills(interaction)

class MapButton(discord.ui.Button):
    """Кнопка для вызова "Карты" (синяя). Делегирует действие методу on_map."""
    def __init__(self, row: int = 0):
        super().__init__(label="Карта", emoji="🗺️", style=discord.ButtonStyle.primary, row=row)

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_map'):
            await self.view.on_map(interaction)
            
class ObserveButton(discord.ui.Button):
    """
    Кнопка для действия "Осмотреться" в локации (серая).
    Делегирует действие методу on_observe.
    """
    def __init__(self, row: int = 1):
        super().__init__(
            label="Осмотреться", 
            emoji="👀", 
            style=discord.ButtonStyle.secondary, 
            row=row
        )

    async def callback(self, interaction: discord.Interaction):
        if hasattr(self.view, 'on_observe'):
            await self.view.on_observe(interaction)
        else:
            await interaction.response.send_message("Здесь нечего осматривать.", ephemeral=True)
