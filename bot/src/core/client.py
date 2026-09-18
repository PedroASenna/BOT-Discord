# Caminho: bot/src/core/client.py

import logging
from typing import Optional, List
import discord
import wavelink
from discord.ext import commands
from bot.src import settings
from bot.src.core import lavalink as lavalink_events
from bot.src.core.scheduler import TaskScheduler
from bot.src.storage.database import Database
from bot.src.data.holidays import get_upcoming_holidays

_logger = logging.getLogger(__name__)

class MusicBot(commands.Bot):
    def __init__(self, guild_ids: Optional[List[int]] = None):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.voice_states = True
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.guild_ids = guild_ids
        self.db = Database()
        self.scheduler = TaskScheduler()

    async def setup_hook(self) -> None:
        _logger.info("Iniciando o setup do bot...")

        # Initialize database
        self.db.connect()

        # Initialize scheduler
        await self.scheduler.start()

        node = wavelink.Node(
            uri=settings.LAVALINK_URI,
            password=settings.LAVALINK_PASSWORD
        )
        await wavelink.Pool.connect(nodes=[node], client=self, cache_capacity=100)

        # Load cogs (music, utility, welcome, holidays, games, events)
        cogs_to_load = ["music", "playlist", "utility", "welcome", "holidays", "games"]
        for cog_name in cogs_to_load:
            try:
                # Import and setup cog with database
                if cog_name in ["welcome", "holidays", "games"]:
                    cog_module = __import__(f"bot.src.commands.{cog_name}", fromlist=[cog_name])
                    await cog_module.setup(self, self.db)
                else:
                    await self.load_extension(f"bot.src.commands.{cog_name}")
                _logger.info(f"Cog '{cog_name}' carregado com sucesso.")
            except Exception as e:
                _logger.error(f"Falha ao carregar o cog '{cog_name}': {e}", exc_info=True)

        # Load server events cog
        try:
            events_module = __import__(f"bot.src.events.server_events", fromlist=["server_events"])
            await events_module.setup(self, self.db)
            _logger.info("Cog 'server_events' carregado com sucesso.")
        except Exception as e:
            _logger.error(f"Falha ao carregar o cog 'server_events': {e}", exc_info=True)

        # Schedule periodic tasks
        await self._schedule_tasks()

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

    async def _schedule_tasks(self):
        """Schedule recurring tasks."""
        async def check_and_notify_holidays():
            """Check for upcoming holidays and notify servers."""
            upcoming = get_upcoming_holidays(days_before=3)
            if upcoming:
                _logger.info(f"Feriado próximo detectado: {upcoming[0]['name']}")
                # TODO: Notify guild notification channels

        # Schedule daily holiday check at 8:00 AM
        self.scheduler.schedule_daily_task(check_and_notify_holidays, hour=8, minute=0, job_id="check_holidays")

        _logger.info("Tarefas agendadas com sucesso")

    async def on_ready(self) -> None:
        _logger.info(f"Bot logado como {self.user.name} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Game(name="/play | 🎵 Música, Feriados e Promoções"))

    async def close(self):
        """Close bot and cleanup resources."""
        _logger.info("Encerrando bot...")
        await self.scheduler.stop()
        self.db.disconnect()
        await super().close()

    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        await lavalink_events.on_wavelink_node_ready(payload)

    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        await lavalink_events.on_wavelink_track_start(payload)

    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        await lavalink_events.on_wavelink_track_end(payload)

    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload):
        await lavalink_events.on_wavelink_track_exception(payload)