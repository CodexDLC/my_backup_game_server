import discord
import math

# Представим, что это класс для вашего предмета, полученный из API
class GameItem:
    def __init__(self, item_id: str, name: str, description: str, quantity: int):
        self.id = item_id
        self.name = name
        self.description = description
        self.quantity = quantity

class PaginatedInventoryView(discord.ui.View):
    def __init__(self, items: list[GameItem], author: discord.User):
        super().__init__(timeout=180)  # Устанавливаем таймаут, например, 3 минуты
        self.items = items
        self.author = author # Сохраняем автора, чтобы только он мог взаимодействовать

        self.items_per_page = 5
        self.current_page = 1
        self.total_pages = math.ceil(len(self.items) / self.items_per_page)
        
        # Динамически создаем и добавляем компоненты при инициализации
        self._update_components()

    # Проверка, чтобы только автор команды мог использовать этот View
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Это не ваш инвентарь!", ephemeral=True)
            return False
        return True

    def _get_current_page_items(self) -> list[GameItem]:
        """Получает срез предметов для текущей страницы."""
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        return self.items[start_index:end_index]

    def _create_embed(self) -> discord.Embed:
        """Создает Embed для текущей страницы."""
        page_items = self._get_current_page_items()
        
        embed = discord.Embed(
            title=f"🎒 Инвентарь - {self.author.display_name}",
            color=discord.Color.blue()
        )
        
        if not page_items:
            embed.description = "Инвентарь пуст."
        else:
            # Формируем список предметов для отображения
            for item in page_items:
                embed.add_field(
                    name=f"{item.name} (x{item.quantity})", 
                    value=item.description, 
                    inline=False
                )
        
        embed.set_footer(text=f"Страница {self.current_page} из {self.total_pages}")
        return embed

    def _update_components(self):
        """Перерисовывает компоненты (кнопки, меню) в зависимости от текущего состояния."""
        self.clear_items() # Очищаем все старые компоненты

        # Добавляем навигационные кнопки
        self.add_item(self.create_nav_button("first", "⏪ В начало", self.current_page == 1))
        self.add_item(self.create_nav_button("prev", "◀️ Назад", self.current_page == 1))
        self.add_item(self.create_nav_button("next", "▶️ Вперед", self.current_page == self.total_pages))
        self.add_item(self.create_nav_button("last", "⏩ В конец", self.current_page == self.total_pages))
        
        # Добавляем выпадающее меню с предметами текущей страницы
        page_items = self._get_current_page_items()
        if page_items:
            self.add_item(self.create_select_menu(page_items))

    def create_nav_button(self, custom_id: str, label: str, disabled: bool) -> discord.ui.Button:
        """Фабрика для создания навигационных кнопок."""
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, custom_id=f"inventory_nav:{custom_id}", disabled=disabled)
        button.callback = self.navigation_callback
        return button

    def create_select_menu(self, items: list[GameItem]) -> discord.ui.Select:
        """Фабрика для создания выпадающего меню."""
        options = [
            discord.SelectOption(label=f"{item.name} (x{item.quantity})", value=item.id, description=item.description[:100])
            for item in items
        ]
        select = discord.ui.Select(placeholder="Выберите предмет для действия...", options=options, custom_id="inventory_select:item")
        select.callback = self.select_callback
        return select

    async def navigation_callback(self, interaction: discord.Interaction):
        """Обрабатывает нажатия на навигационные кнопки."""
        action = interaction.data["custom_id"].split(":")[-1]
        
        if action == "first":
            self.current_page = 1
        elif action == "prev":
            self.current_page -= 1
        elif action == "next":
            self.current_page += 1
        elif action == "last":
            self.current_page = self.total_pages
            
        self._update_components()
        await interaction.response.edit_message(embed=self._create_embed(), view=self)

    async def select_callback(self, interaction: discord.Interaction):
        """Обрабатывает выбор предмета из меню."""
        selected_item_id = interaction.data['values'][0]
        # Здесь вы можете, например, вызвать сервис для получения полной информации о предмете
        # item = await services.game.get_item(selected_item_id)
        
        # Для примера просто выведем сообщение
        await interaction.response.send_message(f"Вы выбрали предмет с ID: `{selected_item_id}`. Теперь вы можете его использовать или одеть.", ephemeral=True)
