import discord
from discord.ext import commands

class WelcomeCog(commands.Cog):
    """Ког для отправки приветственного сообщения новым участникам"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Событие при входе нового участника"""
        channel = discord.utils.get(member.guild.text_channels, name="welcome")  # Ищем канал "welcome"
        if channel:
            await channel.send(f"👋 Привет, {member.mention}! Добро пожаловать на сервер! 🎉")

async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
