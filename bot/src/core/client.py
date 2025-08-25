# Caminho: bot/src/core/client.py

import logging
from typing import Optional, List
import discord
import wavelink
from discord.ext import commands
from bot.src import settings
from bot.src.core import lavalink as lavalink_events

_logger = logging.getLogger(__name__)

class MusicBot(commands.Bot):
    def __init__(self, guild_ids: Optional[List[int]] = None):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_ids = guild_ids

    async def setup_hook(self) -> None:
        _logger.info("Iniciando o setup do bot...")

        node = wavelink.Node(
            uri=settings.LAVALINK_URI, 
            password=settings.LAVALINK_PASSWORD
        )
        await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)

        cogs_to_load = ["music", "playlist", "utility"]
        for cog_name in cogs_to_load:
            try:
                await self.load_extension(f"bot.src.commands.{cog_name}")
                _logger.info(f"Cog '{cog_name}' carregado com sucesso.")
            except Exception as e:
                _logger.error(f"Falha ao carregar o cog '{cog_name}': {e}", exc_info=True)

        if self.guild_ids:
            _logger.info(f"Sincronizando comandos para guilds específicas: {self.guild_ids}")
            for guild_id in self.guild_ids:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
        else:
            _logger.info("Sincronizando comandos globalmente...")
            await self.tree.sync()
        _logger.info("Sincronização de comandos concluída.")

    async def on_ready(self) -> None:
        _logger.info(f"Bot logado como {self.user.name} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="/play | música"))

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        await lavalink_events.on_wavelink_node_ready(payload)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        await lavalink_events.on_wavelink_track_start(payload)

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        await lavalink_events.on_wavelink_track_end(payload)

    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        await lavalink_events.on_wavelink_track_exception(payload)