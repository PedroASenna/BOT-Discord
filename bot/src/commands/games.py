import logging
import discord
from discord import app_commands
from discord.ext import commands
from bot.src.storage.database import Database
from bot.src.services.game_promotions import GamePromotionsService

logger = logging.getLogger(__name__)


class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, db: Database):
        self.bot = bot
        self.db = db
        self.promo_service = GamePromotionsService()

    games_group = app_commands.Group(name="games", description="Comandos de games e promoções")

    @games_group.command(name="search", description="Busca um game com descontos")
    @app_commands.describe(game="Nome do game a buscar")
    async def search_game(self, interaction: discord.Interaction, game: str):
        await interaction.response.defer()

        try:
            # Search for games
            games = await self.promo_service.search_games(game, limit=10)

            if not games:
                await interaction.followup.send(f"❌ Nenhum resultado encontrado para '{game}'", ephemeral=True)
                return

            if len(games) == 1:
                # Se apenas um resultado, já mostra as ofertas
                game_id = games[0]["game_id"]
                deals = await self.promo_service.get_game_deals(game_id)

                await self._send_deals_embed(interaction, games[0]["title"], deals)
            else:
                # Se múltiplos resultados, mostra lista
                embed = discord.Embed(
                    title=f"🎮 Resultados para '{game}'",
                    description="Clique em uma opção para ver as ofertas",
                    color=discord.Color.blue(),
                )

                for idx, g in enumerate(games[:5], 1):
                    embed.add_field(
                        name=f"{idx}. {g['title']}",
                        value=f"ID: {g['game_id']}",
                        inline=False,
                    )

                embed.set_footer(text="Use `/games deals <nome>` para buscar diretamente")
                await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao buscar games: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @games_group.command(name="deals", description="Mostra games com grandes descontos")
    @app_commands.describe(discount="Percentual mínimo de desconto (padrão: 70)")
    async def search_deals(self, interaction: discord.Interaction, discount: int = 70):
        await interaction.response.defer()

        try:
            if discount < 0 or discount > 100:
                await interaction.followup.send("❌ Desconto deve estar entre 0 e 100", ephemeral=True)
                return

            deals = await self.promo_service.search_deals(min_discount=discount)

            if not deals:
                await interaction.followup.send(
                    f"❌ Nenhuma promoção encontrada com {discount}% de desconto",
                    ephemeral=True,
                )
                return

            # Create paginated response
            embeds = []
            for deal in deals[:10]:
                embed = discord.Embed(
                    title=deal["title"],
                    url=deal["url"],
                    color=discord.Color.gold(),
                )
                embed.add_field(
                    name="🏪 Loja",
                    value=deal["store"],
                    inline=True,
                )
                embed.add_field(
                    name="💵 Preço",
                    value=f"R$ {deal['price']:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name="💰 Preço Original",
                    value=f"R$ {deal['retail_price']:.2f}",
                    inline=True,
                )
                embed.add_field(
                    name="🔥 Desconto",
                    value=f"{deal['discount']}%",
                    inline=True,
                )
                embed.set_thumbnail(url=deal.get("thumb"))
                embed.set_footer(text="Clique no título para acessar a oferta")

                embeds.append(embed)

            # Send first embed, mention there are more
            if len(embeds) > 1:
                embeds[0].description = f"Mostrando 1 de {len(embeds)} ofertas"

            await interaction.followup.send(embed=embeds[0])

            # Send additional embeds if needed
            for embed in embeds[1:5]:
                await interaction.channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao buscar ofertas: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @games_group.command(name="follow", description="Recebe notificações sobre promoções de um game")
    @app_commands.describe(game="Nome do game para seguir")
    async def follow_game(self, interaction: discord.Interaction, game: str):
        await interaction.response.defer()

        try:
            success = self.db.add_game_follower(interaction.user.id, interaction.guild.id, game)

            if success:
                embed = discord.Embed(
                    title=f"✅ Você está seguindo '{game}'",
                    description="Você receberá notificações quando houver promoções",
                    color=discord.Color.green(),
                )
                await interaction.followup.send(embed=embed)
                logger.info(f"Usuário {interaction.user.name} está seguindo {game}")
            else:
                embed = discord.Embed(
                    title="⚠️ Você já está seguindo este game",
                    color=discord.Color.orange(),
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Erro ao seguir game: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    @games_group.command(name="trending", description="Mostra games em alta com descontos")
    async def trending_games(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            deals = await self.promo_service.search_deals(min_discount=50)

            if not deals:
                await interaction.followup.send("❌ Nenhuma promoção encontrada no momento", ephemeral=True)
                return

            embed = discord.Embed(
                title="🔥 Games em Alta com Desconto",
                description="Top games com maiores descontos",
                color=discord.Color.red(),
            )

            for idx, deal in enumerate(deals[:5], 1):
                value = f"**{deal['store']}** • 🔥 {deal['discount']}% OFF\n"
                value += f"R$ {deal['price']:.2f} (era R$ {deal['retail_price']:.2f})"

                embed.add_field(
                    name=f"{idx}. {deal['title']}",
                    value=value,
                    inline=False,
                )

            embed.set_footer(text="Use `/games deals 70` para mais ofertas")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Erro ao buscar games em alta: {e}")
            await interaction.followup.send("❌ Erro ao processar comando", ephemeral=True)

    async def _send_deals_embed(self, interaction: discord.Interaction, game_title: str, deals: list):
        """Helper para enviar embed de ofertas."""
        if not deals:
            embed = discord.Embed(
                title=game_title,
                description="❌ Nenhuma oferta encontrada no momento",
                color=discord.Color.greyple(),
            )
            await interaction.followup.send(embed=embed)
            return

        for deal in deals[:5]:
            embed = discord.Embed(
                title=game_title,
                url=deal["url"],
                color=discord.Color.green(),
            )
            embed.add_field(
                name="🏪 Loja",
                value=deal["store_name"],
                inline=True,
            )
            embed.add_field(
                name="💵 Preço",
                value=f"R$ {deal['price']:.2f}",
                inline=True,
            )
            embed.add_field(
                name="🔥 Desconto",
                value=f"{deal['discount']}%",
                inline=True,
            )
            embed.set_footer(text="Clique no título para acessar a oferta")

            await interaction.channel.send(embed=embed)


async def setup(bot: commands.Bot, db: Database):
    await bot.add_cog(GamesCog(bot, db))
