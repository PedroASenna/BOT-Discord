# Caminho do arquivo: bot/src/core/manager.py

import asyncio
import logging
from collections import deque
from typing import Optional

import discord
import wavelink
from discord.ext import commands

from bot.src.core.models import LoopMode

_logger = logging.getLogger(__name__)

class MusicManager:
    """Gerencia o estado de música para uma única guild."""

    def __init__(self, guild_id: int, bot: commands.Bot):
        self.guild_id = guild_id
        self.bot = bot
        self.queue: deque[wavelink.Playable] = deque()
        self.loop_mode: LoopMode = LoopMode.OFF
        self.now_playing_message: Optional[discord.Message] = None
        self.last_interaction: Optional[discord.Interaction] = None
        self._auto_disconnect_task: Optional[asyncio.Task] = None

    @property
    def player(self) -> Optional[wavelink.Player]:
        """Retorna o player da guild, se existir."""
        guild = self.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    async def connect(self, channel: discord.VoiceChannel) -> wavelink.Player:
        """Conecta a um canal de voz."""
        player = await channel.connect(cls=wavelink.Player)
        _logger.info(f"Conectado ao canal de voz {channel.name} na guild {self.guild_id}.")
        return player

    async def disconnect(self) -> None:
        """Desconecta do canal de voz e limpa o estado."""
        if self.player:
            await self.player.disconnect()
            _logger.info(f"Desconectado da guild {self.guild_id}.")
        self.clear_queue()
        self.loop_mode = LoopMode.OFF
        if self._auto_disconnect_task:
            self._auto_disconnect_task.cancel()

    def add_to_queue(self, track: wavelink.Playable, requester: discord.Member):
        """Adiciona uma música à fila."""
        # CORREÇÃO 1: Usar sintaxe de objeto (ponto) em vez de dicionário (colchetes)
        track.extras.requester = requester.mention
        self.queue.append(track)
        _logger.info(f"'{track.title}' adicionada à fila na guild {self.guild_id}.")

    async def start_playback(self):
        """Inicia o playback se não houver uma música carregada e houver itens na fila."""
        if self.queue and not self.player.current:
            await self.play_next_track()

    async def play_next_track(self):
        """Toca a próxima música na fila, gerenciando o modo de loop."""
        if self._auto_disconnect_task:
            self._auto_disconnect_task.cancel()

        if not self.queue and self.loop_mode is not LoopMode.TRACK:
            _logger.info(f"Fila vazia na guild {self.guild_id}. Iniciando auto-disconnect.")
            self._auto_disconnect_task = asyncio.create_task(self._auto_disconnect())
            return

        current_track = self.player.current

        next_track: Optional[wavelink.Playable] = None
        if self.loop_mode == LoopMode.TRACK and current_track:
            next_track = current_track
        elif self.queue:
            if self.loop_mode == LoopMode.QUEUE and current_track:
                self.queue.append(current_track)
            next_track = self.queue.popleft()

        if next_track:
            await self.player.play(next_track)
            _logger.info(f"Tocando '{next_track.title}' na guild {self.guild_id}.")

    async def on_track_start(self, track: wavelink.Playable):
        """Callback para quando uma música começa."""
        if self.last_interaction:
            # CORREÇÃO 2: Usar getattr para ler a propriedade de forma segura
            requester = getattr(track.extras, 'requester', 'N/A')
            embed = discord.Embed(
                title="🎵 Tocando Agora",
                description=f"**[{track.title}]({track.uri})**\nPedido por: {requester}",
                color=discord.Color.green()
            )
            try:
                if self.now_playing_message:
                    await self.now_playing_message.delete()
                self.now_playing_message = await self.last_interaction.channel.send(embed=embed)
            except (discord.NotFound, discord.HTTPException):
                self.now_playing_message = None

    async def on_track_error(self, track: wavelink.Playable, error: Exception):
        """Callback para erro na música."""
        if self.last_interaction and self.last_interaction.channel:
            await self.last_interaction.channel.send(
                f"❌ Ocorreu um erro ao tentar tocar `{track.title}`: `{error}`"
            )
        await self.play_next_track()

    def clear_queue(self):
        """Limpa a fila de músicas."""
        self.queue.clear()
        _logger.info(f"Fila limpa para a guild {self.guild_id}.")

    async def _auto_disconnect(self):
        """Tarefa que desconecta o bot após um período de inatividade."""
        await asyncio.sleep(120)  # 2 minutos
        if self.player and not self.player.is_playing() and not self.queue:
            if self.last_interaction and self.last_interaction.channel:
                await self.last_interaction.channel.send("👋 Inativo por 2 minutos. Desconectando...")
            await self.disconnect()