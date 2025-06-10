import discord
from discord.ext import commands

from Discord_API.api_route_function.system.system_accaunt_api import DiscordCreateAccount
from Discord_API.ui_templates.register_button import RegistrationView

class RegistrationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="начать")
    async def start_registration(self, ctx):
        """Отправляет DM пользователю с кнопками"""
        user = ctx.author
        discord_account = DiscordCreateAccount(user_id=str(user.id), username=user.name, avatar_url=str(user.avatar))

        account_data = await discord_account.get_account_discord(user.id)

        embed = discord.Embed(title="Регистрация в игре", color=discord.Color.blue())

        if account_data.get("status") == "found":
            embed.description = "Ваш аккаунт уже зарегистрирован. Нажмите 'Войти'."
        else:
            embed.description = "У вас нет аккаунта. Нажмите 'Регистрация', чтобы создать новый."

        view = RegistrationView(user.id)
        await user.send(embed=embed, view=view)

    @commands.command(name="register_user")
    async def register_user(self, interaction: discord.Interaction):
        """Создаёт аккаунт и отправляет кнопку 'Создать персонажа'"""
        user = interaction.user
        discord_account = DiscordCreateAccount(user_id=str(user.id), username=user.name, avatar_url=str(user.avatar))

        response = discord_account.create_account()  # 🔥 Запрос в API для регистрации

        if response.get("status") == "created":  # ✅ Аккаунт успешно создан
            embed = discord.Embed(title="Регистрация завершена!", description="Теперь создайте первого персонажа!", color=discord.Color.green())
            view = RegistrationView(user.id)  # 🔥 Добавляем кнопку "Создать персонажа"
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        else:  # ❌ Ошибка регистрации
            await interaction.response.send_message("Ошибка регистрации!", ephemeral=True)

async def setup(bot):
    """Добавляет ког в бота."""
    await bot.add_cog(RegistrationCog(bot))
