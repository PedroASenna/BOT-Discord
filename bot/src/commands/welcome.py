import logging
import discord
from discord import app_commands
from discord.ext import commands
from bot.src.storage.database import Database

logger = logging.getLogger(__name__)


class WelcomeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    welcome_group = app_commands.Group(name="welcome", description="Comandos de boas-vindas")

    @welcome_group.command(name="set-message", description="Define a mensagem de boas-vindas")
    @app_commands.describe(message="Mensagem de boas-vindas (use {mention}, {username}, {server}, {total_members})")
    @commands.has_permissions(administrator=True)
    async def set_message(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()

        # Get the interaction channel as default
        channel = interaction.channel

        if not channel:
            await interaction.followup.send("❌ Erro: Não foi possível determinar o canal", ephemeral=True)
            return

        success = self.db.save_welcome_message(interaction.guild.id, channel.id, message)

        if success:
            embed = discord.Embed(
                title="✅ Boas-vindas Configuradas",
                description=f"Mensagem: {message}",
                color=discord.Color.green(),
            )
            embed.add_field(name="Canal", value=channel.mention)
            embed.add_field(name="Status", value="🟢 Ativado")
            await interaction.followup.send(embed=embed)
            logger.info(f"Mensagem de boas-vindas definida para servidor {interaction.guild.name}")
        else:
            await interaction.followup.send("❌ Erro ao salvar configuração", ephemeral=True)

    @welcome_group.command(name="set-channel", description="Define o canal para enviar boas-vindas")
    @app_commands.describe(channel="Canal para enviar boas-vindas")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer()

        try:
            # Get current welcome config or create default
            current_config = self.db.get_welcome_message(interaction.guild.id)
            message = current_config.get("message", "Bem-vindo, {mention}!") if current_config else "Bem-vindo, {mention}!"

            success = self.db.save_welcome_message(interaction.guild.id, channel.id, message)

            if success:
                embed = discord.Embed(
                    title="✅ Canal de Boas-vindas Configurado",
                    description=f"Novo canal: {channel.mention}",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                logger.info(f"Canal de boas-vindas definido para {channel.name} no servidor {interaction.guild.name}")
            else:
                await interaction.followup.send("❌ Erro ao salvar configuração", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao definir canal de boas-vindas: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @welcome_group.command(name="enable", description="Ativa as boas-vindas automáticas")
    @commands.has_permissions(administrator=True)
    async def enable(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            current_config = self.db.get_welcome_message(interaction.guild.id)

            if not current_config:
                await interaction.followup.send(
                    "⚠️ Configure as boas-vindas primeiro com `/welcome set-message`",
                    ephemeral=True,
                )
                return

            channel = interaction.guild.get_channel(current_config.get("channel_id"))
            message = current_config.get("message", "Bem-vindo, {mention}!")

            self.db.save_welcome_message(interaction.guild.id, channel.id, message)

            embed = discord.Embed(
                title="✅ Boas-vindas Ativadas",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao ativar boas-vindas: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @welcome_group.command(name="list", description="Lista os últimos membros que entraram")
    async def list_welcome(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            history = self.db.get_welcome_history(interaction.guild.id, limit=10)

            if not history:
                await interaction.followup.send("📭 Nenhum membro registrado ainda", ephemeral=True)
                return

            embed = discord.Embed(
                title="📜 Histórico de Boas-vindas",
                description="Últimos membros que entraram:",
                color=discord.Color.blue(),
            )

            welcome_list = "\n".join(
                [
                    f"• **{h['username']}** (ID: {h['user_id']}) - {h['sent_at']}"
                    for h in history
                ]
            )

            embed.add_field(name="Membros", value=welcome_list, inline=False)
            embed.set_footer(text=f"Total: {len(history)} registros")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao listar histórico de boas-vindas: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(WelcomeCog(bot, db))
