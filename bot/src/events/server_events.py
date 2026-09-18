import logging
import discord
from discord.ext import commands
from bot.src.storage.database import Database

logger = logging.getLogger(__name__)


class ServerEventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Dispara quando um novo membro entra no servidor."""
        try:
            guild = member.guild
            welcome_config = self.db.get_welcome_message(guild.id)

            if not welcome_config:
                logger.debug(f"Sem configuração de boas-vindas para servidor {guild.id}")
                return

            # Obtém o canal de notificações
            channel_id = welcome_config.get("channel_id")

            if not channel_id:
                logger.warning(f"Sem canal de notificações definido para servidor {guild.id}")
                return

            channel = guild.get_channel(channel_id)

            if not channel:
                logger.warning(f"Canal {channel_id} não encontrado no servidor {guild.id}")
                return

            # Prepare welcome message
            message_template = welcome_config.get("message", "Bem-vindo, {mention}!")
            message = message_template.format(
                mention=member.mention,
                username=member.name,
                server=guild.name,
                total_members=guild.member_count,
            )

            # Send welcome embed
            embed = discord.Embed(
                title=f"Bem-vindo ao {guild.name}! 👋",
                description=message,
                color=discord.Color.green(),
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.add_field(
                name="Informações",
                value=f"Você é o membro #{guild.member_count}",
                inline=False,
            )
            embed.set_footer(text=f"ID: {member.id}")

            await channel.send(embed=embed)

            # Save to history
            self.db.save_welcome_history(guild.id, member.id, member.name)
            logger.info(f"Mensagem de boas-vindas enviada para {member.name} no servidor {guild.name}")

        except discord.Forbidden:
            logger.error(f"Permissão negada para enviar mensagem de boas-vindas no servidor {member.guild.id}")
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de boas-vindas: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Dispara quando um membro sai do servidor."""
        try:
            logger.info(f"Membro {member.name} saiu do servidor {member.guild.name}")
        except Exception as e:
            logger.error(f"Erro ao processar saída de membro: {e}")


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(ServerEventsCog(bot, db))
