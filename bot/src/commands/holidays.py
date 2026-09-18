import logging
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
from bot.src.storage.database import Database
from bot.src.data.holidays import get_next_holidays, get_upcoming_holidays, is_holiday_today

logger = logging.getLogger(__name__)


class HolidaysCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    holidays_group = app_commands.Group(name="holidays", description="Comandos de feriados")

    @holidays_group.command(name="next", description="Mostra os próximos feriados")
    @app_commands.describe(limit="Quantidade de feriados a mostrar (padrão: 5)")
    async def next_holidays(self, interaction: discord.Interaction, limit: int = 5):
        await interaction.response.defer()

        try:
            holidays = get_next_holidays(limit=min(limit, 10))

            if not holidays:
                await interaction.followup.send("📭 Nenhum feriado encontrado", ephemeral=True)
                return

            embed = discord.Embed(
                title="🎉 Próximos Feriados",
                description=f"Mostrando os próximos {len(holidays)} feriados",
                color=discord.Color.purple(),
            )

            for holiday in holidays:
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
                formatted_date = holiday_date.strftime("%d/%m/%Y (%A)")
                days = holiday["days_until"]

                if days == 0:
                    time_str = "🔴 HOJE"
                elif days == 1:
                    time_str = "⏰ AMANHÃ"
                else:
                    time_str = f"📅 Em {days} dias"

                embed.add_field(
                    name=f"{holiday['name']} {time_str}",
                    value=formatted_date,
                    inline=False,
                )

            embed.set_footer(text="Feriados brasileiros fixos e móveis")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao buscar próximos feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @holidays_group.command(name="today", description="Verifica se hoje é feriado")
    async def holiday_today(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            holiday = is_holiday_today()

            if holiday:
                embed = discord.Embed(
                    title=f"🎉 {holiday['name']}",
                    description="Hoje é feriado!",
                    color=discord.Color.gold(),
                )
                embed.add_field(
                    name="Data",
                    value=datetime.now().strftime("%d/%m/%Y"),
                    inline=False,
                )
                await interaction.followup.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="📅 Dia Normal",
                    description="Hoje não é feriado",
                    color=discord.Color.greyple(),
                )
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao verificar feriado de hoje: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @holidays_group.command(name="reminder", description="Define alertas de feriados (com antecedência)")
    @app_commands.describe(days="Dias de antecedência (padrão: 3)")
    @commands.has_permissions(administrator=True)
    async def set_reminder(self, interaction: discord.Interaction, days: int = 3):
        await interaction.response.defer()

        try:
            if days < 1 or days > 30:
                await interaction.followup.send("❌ Dias deve estar entre 1 e 30", ephemeral=True)
                return

            # Set notification channel
            self.db.set_notification_channel(interaction.guild.id, interaction.channel.id, "holidays")

            embed = discord.Embed(
                title="✅ Alertas de Feriados Configurados",
                description=f"Você receberá alertas **{days} dias** antes dos feriados",
                color=discord.Color.green(),
            )
            embed.add_field(name="Canal", value=interaction.channel.mention)
            embed.add_field(
                name="Próximos Feriados com Alerta",
                value="Use `/holidays next` para ver",
                inline=False,
            )
            await interaction.followup.send(embed=embed)
            logger.info(f"Alertas de feriados configurados para servidor {interaction.guild.name}")

        except Exception as e:
            logger.error(f"Erro ao configurar alertas de feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @holidays_group.command(name="notify", description="Envia notificação de feriados próximos")
    @commands.has_permissions(administrator=True)
    async def notify_holidays(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            upcoming = get_upcoming_holidays(days_before=3)

            if not upcoming:
                await interaction.followup.send("✅ Nenhum feriado com antecedência de 3 dias", ephemeral=True)
                return

            embed = discord.Embed(
                title="🎉 Feriados Próximos (próximos 3 dias)",
                color=discord.Color.gold(),
            )

            for holiday in upcoming:
                holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
                formatted_date = holiday_date.strftime("%d/%m/%Y (%A)")
                days = holiday["days_until"]

                emoji = "🔴" if days == 0 else "⏰" if days == 1 else "📅"
                embed.add_field(
                    name=f"{emoji} {holiday['name']}",
                    value=f"{formatted_date} (em {days} dias)",
                    inline=False,
                )

            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ Notificação enviada", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao enviar notificação de feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(HolidaysCog(bot, db))
