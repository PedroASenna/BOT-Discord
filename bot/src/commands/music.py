import logging
import discord
import wavelink
from discord import app_commands
from discord.ext import commands

from bot.src.core.lavalink import get_music_manager
from bot.src.core.models import LoopMode
from bot.src.views.pagination import PaginationView

_logger = logging.getLogger(__name__)


class MusicCog(commands.Cog, name="Música"):
    """Comandos para tocar música."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Função crucial que verifica se o usuário está em um canal de voz
    # ANTES de executar qualquer comando deste grupo.
    async def cog_check(self, interaction: discord.Interaction) -> bool:
        """Verifica se o usuário está em um canal de voz antes de cada comando."""
        if not interaction.user.voice:
            await interaction.response.send_message(
                "❌ Você precisa estar em um canal de voz para usar este comando.",
                ephemeral=True
            )
            return False
        return True

    @app_commands.command(name="play", description="Toca uma música ou adiciona à fila.")
    @app_commands.describe(consulta="Nome ou URL da música (YouTube, SoundCloud).")
    async def play(self, interaction: discord.Interaction, *, consulta: str):
        # Adia a resposta para o Discord saber que recebemos o comando.
        await interaction.response.defer(thinking=True)

        manager = get_music_manager(interaction.guild_id, self.bot)
        manager.last_interaction = interaction

        # Conecta ao canal de voz do usuário se não estiver conectado.
        player = manager.player or await manager.connect(interaction.user.voice.channel)

        if not player:
            await interaction.followup.send("Não foi possível conectar ao canal de voz.", ephemeral=True)
            return

        # CORREÇÃO FINAL: Usa a busca do YouTube de forma explícita.
        tracks: wavelink.Search = await wavelink.Playable.search(consulta, source=wavelink.TrackSource.YouTube)

        if not tracks:
            await interaction.followup.send(f"Nenhum resultado encontrado para `{consulta}`.", ephemeral=True)
            return

        track = tracks[0]
        manager.add_to_queue(track, interaction.user)

        embed = discord.Embed(
            title="✅ Adicionado à Fila",
            description=f"**[{track.title}]({track.uri})**",
            color=discord.Color.blurple()
        ).set_thumbnail(url=track.artwork)
        await interaction.followup.send(embed=embed)

        await manager.start_playback()

    @app_commands.command(name="skip", description="Pula para a próxima música na fila.")
    async def skip(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)
        if not manager.player or not manager.player.is_playing():
            await interaction.response.send_message("Não há nada tocando no momento.", ephemeral=True)
            return

        await manager.player.skip(force=True)
        await interaction.response.send_message("⏭️ Música pulada.")

    @app_commands.command(name="pause", description="Pausa a música atual.")
    async def pause(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)
        if not manager.player or not manager.player.is_playing():
            await interaction.response.send_message("Não há nada tocando no momento.", ephemeral=True)
            return

        await manager.player.pause(True)
        await interaction.response.send_message("⏸️ Música pausada.")

    @app_commands.command(name="resume", description="Continua a tocar a música pausada.")
    async def resume(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)
        if not manager.player or not manager.player.is_paused():
            await interaction.response.send_message("A música não está pausada.", ephemeral=True)
            return

        await manager.player.pause(False)
        await interaction.response.send_message("▶️ Música retomada.")

    @app_commands.command(name="stop", description="Para a música e limpa a fila.")
    async def stop(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)
        if not manager.player:
            await interaction.response.send_message("O bot não está tocando nada.", ephemeral=True)
            return

        manager.clear_queue()
        await manager.player.stop(force=True)
        await interaction.response.send_message("⏹️ Player parado e fila limpa.")

    @app_commands.command(name="leave", description="Desconecta o bot do canal de voz.")
    async def leave(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)
        if not manager.player:
            await interaction.response.send_message("O bot não está conectado a um canal.", ephemeral=True)
            return

        await manager.disconnect()
        await interaction.response.send_message("👋 Desconectado com sucesso!")

    @app_commands.command(name="queue", description="Mostra a fila de músicas.")
    async def queue(self, interaction: discord.Interaction):
        manager = get_music_manager(interaction.guild_id, self.bot)

        if not manager.queue and (not manager.player or not manager.player.current):
            await interaction.response.send_message("A fila está vazia.", ephemeral=True)
            return

        pages = []
        queue_list = list(manager.queue)
        items_per_page = 10
        
        # Gera a primeira página com a música atual
        current_track_text = ""
        if manager.player and manager.player.current:
            track = manager.player.current
            requester = getattr(track.extras, 'requester', 'N/A')
            current_track_text = f"**▶ Tocando Agora:** [{track.title}]({track.uri})\nPedido por: {requester}\n\n"
        
        # Gera as páginas com a fila
        page_chunks = [queue_list[i:i + items_per_page] for i in range(0, len(queue_list), items_per_page)]
        if not page_chunks: # Se a fila estiver vazia mas algo estiver tocando
             pages.append(discord.Embed(title="🎵 Fila de Músicas", description=current_track_text, color=discord.Color.purple()))
        else:
            for i, chunk in enumerate(page_chunks):
                page_content = current_track_text if i == 0 else ""
                start_index = i * items_per_page
                for index, track in enumerate(chunk, start=start_index + 1):
                    requester = getattr(track.extras, 'requester', 'N/A')
                    page_content += f"`{index}.` [{track.title}]({track.uri})\nPedido por: {requester}\n"

                embed = discord.Embed(
                    title=f"🎵 Fila de Músicas (Página {i+1}/{len(page_chunks)})",
                    description=page_content,
                    color=discord.Color.purple()
                )
                embed.set_footer(text=f"Total: {len(queue_list)} músicas")
                pages.append(embed)

        view = PaginationView(pages)
        await interaction.response.send_message(embed=pages[0], view=view)


    @app_commands.command(name="loop", description="Define o modo de repetição.")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Desativado", value="off"),
        app_commands.Choice(name="Música Atual", value="track"),
        app_commands.Choice(name="Fila Inteira", value="queue"),
    ])
    async def loop(self, interaction: discord.Interaction, modo: app_commands.Choice[str]):
        manager = get_music_manager(interaction.guild_id, self.bot)

        if modo.value == "off":
            manager.loop_mode = LoopMode.OFF
        elif modo.value == "track":
            manager.loop_mode = LoopMode.TRACK
        elif modo.value == "queue":
            manager.loop_mode = LoopMode.QUEUE

        await interaction.response.send_message(f"🔁 Modo de repetição definido para: **{manager.loop_mode.value}**")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))