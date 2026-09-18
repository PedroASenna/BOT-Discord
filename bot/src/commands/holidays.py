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
    @app_commands.describe(limit="Quantidade de feriados a mostrar (padrão: 5)", municipal="Incluir feriados municipais? (S/N)")
    async def next_holidays(self, interaction: discord.Interaction, limit: int = 5, municipal: str = "N"):
        await interaction.response.defer()

        try:
            include_municipal = municipal.upper() in ["S", "SIM"]
            holidays = get_next_holidays(limit=min(limit, 10), include_municipal=include_municipal, city="Imperatriz")

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

                scope_badge = "🏙️ Feriado Municipal" if holiday.get("scope") == "municipal" else "🇧🇷 Feriado Nacional"

                embed.add_field(
                    name=f"{holiday['name']} {time_str}",
                    value=f"{formatted_date}\n*{scope_badge}*",
                    inline=False,
                )

            footer_text = "Incluindo feriados de Imperatriz" if include_municipal else "Apenas feriados nacionais"
            embed.set_footer(text=f"Feriados brasileiros fixos e móveis • {footer_text}")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao buscar próximos feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @holidays_group.command(name="today", description="Verifica se hoje é feriado")
    @app_commands.describe(municipal="Incluir feriados municipais? (S/N)")
    async def holiday_today(self, interaction: discord.Interaction, municipal: str = "N"):
        await interaction.response.defer()

        try:
            include_municipal = municipal.upper() in ["S", "SIM"]
            holiday = is_holiday_today(include_municipal=include_municipal, city="Imperatriz")

            if holiday:
                scope_badge = "🏙️ Feriado Municipal" if holiday.get("scope") == "municipal" else "🇧🇷 Feriado Nacional"
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
                embed.add_field(
                    name="Tipo",
                    value=scope_badge,
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
    @app_commands.describe(municipal="Incluir feriados municipais? (S/N)")
    @commands.has_permissions(administrator=True)
    async def notify_holidays(self, interaction: discord.Interaction, municipal: str = "N"):
        await interaction.response.defer()

        try:
            include_municipal = municipal.upper() in ["S", "SIM"]
            upcoming = get_upcoming_holidays(days_before=3, include_municipal=include_municipal, city="Imperatriz")

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

                scope_badge = "🏙️" if holiday.get("scope") == "municipal" else "🇧🇷"
                emoji = "🔴" if days == 0 else "⏰" if days == 1 else "📅"
                embed.add_field(
                    name=f"{emoji} {scope_badge} {holiday['name']}",
                    value=f"{formatted_date} (em {days} dias)",
                    inline=False,
                )

            await interaction.channel.send(embed=embed)
            await interaction.followup.send("✅ Notificação enviada", ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao enviar notificação de feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @holidays_group.command(name="config", description="Configura preferências de feriados do servidor")
    @app_commands.describe(show_municipal="Mostrar feriados municipais por padrão? (sim/não)")
    @commands.has_permissions(administrator=True)
    async def config_holidays(self, interaction: discord.Interaction, show_municipal: str = "não"):
        await interaction.response.defer()

        try:
            guild_id = interaction.guild.id
            include_municipal = show_municipal.lower() in ["sim", "s", "yes", "y"]

            self.db.execute(
                """
                INSERT OR REPLACE INTO server_config (guild_id, key, value)
                VALUES (?, ?, ?)
                """,
                (guild_id, "show_municipal_holidays", "true" if include_municipal else "false")
            )

            embed = discord.Embed(
                title="✅ Configurações de Feriados Atualizadas",
                description=f"Feriados municipais: {'✅ Habilitados' if include_municipal else '❌ Desabilitados'}",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Detalhes",
                value="Os comandos de feriados agora mostrarão municipais por padrão" if include_municipal else "Os comandos mostrarão apenas feriados nacionais",
                inline=False,
            )
            await interaction.followup.send(embed=embed)
            logger.info(f"Configurações de feriados atualizadas para servidor {interaction.guild.name}")

        except Exception as e:
            logger.error(f"Erro ao configurar feriados: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(HolidaysCog(bot, db))
