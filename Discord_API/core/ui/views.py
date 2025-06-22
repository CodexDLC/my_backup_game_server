import discord

# Этот класс можно рассматривать как шаблон для всех ваших будущих интерфейсов.
# Он является "постоянным" (persistent), так как timeout=None,
# и будет работать даже после перезапуска бота.
class FullUIPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        # Динамически добавляем кнопку-ссылку.
        # Это полезно, если URL должен генерироваться при создании View.
        self.add_item(discord.ui.Button(label="Сайт проекта", url="https://github.com/"))

    # 1. Пример кнопок с разными стилями
    @discord.ui.button(label="Основная", style=discord.ButtonStyle.primary, custom_id="ui_panel:primary_button")
    async def primary_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Вы нажали на 'Основную' кнопку.", ephemeral=True)

    @discord.ui.button(label="Вторичная", style=discord.ButtonStyle.secondary, custom_id="ui_panel:secondary_button")
    async def secondary_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Вы нажали на 'Вторичную' кнопку.", ephemeral=True)

    @discord.ui.button(label="Успех", style=discord.ButtonStyle.success, custom_id="ui_panel:success_button")
    async def success_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message("Действие выполнено успешно!", ephemeral=True)

    # 2. Кнопка с эмодзи и опасным стилем
    @discord.ui.button(label="Опасно!", emoji="🔥", style=discord.ButtonStyle.danger, custom_id="ui_panel:danger_button")
    async def danger_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Перед опасным действием можно добавить модальное окно для подтверждения
        button.disabled = True # Отключаем кнопку после нажатия, чтобы избежать повторных кликов
        await interaction.message.edit(view=self)
        await interaction.response.send_message("Вы активировали опасное действие!", ephemeral=True)
        
    # 3. Отключенная (disabled) кнопка
    @discord.ui.button(label="Нельзя нажать", style=discord.ButtonStyle.secondary, disabled=True, custom_id="ui_panel:disabled_button")
    async def disabled_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        # Этот код никогда не выполнится
        pass

    # 4. Выпадающее меню для выбора ОДНОГО варианта
    @discord.ui.select(
        placeholder="Выберите ваш класс...",
        min_values=1,
        max_values=1,
        custom_id="ui_panel:class_select",
        options=[
            discord.SelectOption(label="Воин", description="Мастер ближнего боя.", emoji="⚔️"),
            discord.SelectOption(label="Маг", description="Повелитель стихий.", emoji="🧙"),
            discord.SelectOption(label="Лучник", description="Меткий стрелок.", emoji="🏹")
        ]
    )
    async def class_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        # `interaction.values` содержит список выбранных значений. Так как у нас max_values=1, в списке будет 1 элемент.
        selected_class = interaction.values[0]
        await interaction.response.send_message(f"Вы выбрали класс: **{selected_class}**", ephemeral=True)

    # 5. Выпадающее меню для выбора НЕСКОЛЬКИХ вариантов
    @discord.ui.select(
        placeholder="Выберите до 3-х навыков...",
        min_values=1,
        max_values=3,
        custom_id="ui_panel:skill_select",
        options=[
            discord.SelectOption(label="Сила", value="skill_strength"),
            discord.SelectOption(label="Ловкость", value="skill_agility"),
            discord.SelectOption(label="Интеллект", value="skill_intelligence"),
            discord.SelectOption(label="Выносливость", value="skill_stamina"),
            discord.SelectOption(label="Харизма", value="skill_charisma")
        ]
    )
    async def skill_select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        # interaction.values вернет список ['skill_agility', 'skill_charisma'] и т.д.
        # Мы используем ', '.join() для красивого вывода
        selected_skills = ', '.join(interaction.values)
        await interaction.response.send_message(f"Вы выбрали навыки: **{selected_skills}**", ephemeral=True)
