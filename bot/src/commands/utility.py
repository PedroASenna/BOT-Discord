import time
import discord
from discord import app_commands
from discord.ext import commands

class UtilityCog(commands.Cog, name="Utilidade"):
    """Comandos úteis e de informação."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Verifica a latência do bot.")
    async def ping(self, interaction: discord.Interaction):
        bot_latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latência: `{bot_latency}ms`")

    @app_commands.command(name="stats", description="Mostra estatísticas do bot.")
    async def stats(self, interaction: discord.Interaction):
        uptime_seconds = time.time() - self.start_time
        uptime_str = time.strftime("%d dias, %H horas, %M minutos, %S segundos", time.gmtime(uptime_seconds))
        
        embed = discord.Embed(title="📊 Estatísticas do Bot", color=discord.Color.blue())
        embed.add_field(name="Uptime", value=uptime_str, inline=False)
        embed.add_field(name="Servidores", value=str(len(self.bot.guilds)))
        # Outras métricas podem ser adicionadas aqui
        
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))