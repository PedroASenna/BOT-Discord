import logging
from typing import Dict

import wavelink
from discord.ext import commands

from bot.src.core.manager import MusicManager

_logger = logging.getLogger(__name__)

# Mapeia IDs de Guild para instâncias de MusicManager
music_managers: Dict[int, MusicManager] = {}

def get_music_manager(guild_id: int, bot: commands.Bot) -> MusicManager:
    """Retorna o MusicManager para uma guild, criando um se não existir."""
    if guild_id not in music_managers:
        music_managers[guild_id] = MusicManager(guild_id, bot)
        _logger.info(f"Novo MusicManager criado para a guild {guild_id}.")
    return music_managers[guild_id]

async def on_wavelink_node_ready(payload: wavelink.NodeReadyEventPayload) -> None:
    """Evento disparado quando um nó do Lavalink está pronto."""
    _logger.info(f"Nó do Wavelink '{payload.node.identifier}' está pronto.")

async def on_wavelink_track_start(payload: wavelink.TrackStartEventPayload) -> None:
    """Evento disparado quando uma música começa a tocar."""
    manager = music_managers.get(payload.player.guild.id)
    if manager:
        await manager.on_track_start(payload.track)

async def on_wavelink_track_end(payload: wavelink.TrackEndEventPayload) -> None:
    """Evento disparado quando uma música termina."""
    manager = music_managers.get(payload.player.guild.id)
    # CORREÇÃO: A razão agora é uma string, não um objeto.
    if manager and payload.reason == "FINISHED":
        await manager.play_next_track()

async def on_wavelink_track_exception(payload: wavelink.TrackExceptionEventPayload) -> None:
    """Evento disparado em caso de erro ao tocar."""
    _logger.error(f"Erro ao tocar a música: {payload.exception}")
    manager = music_managers.get(payload.player.guild.id)
    if manager:
        await manager.on_track_error(payload.track, payload.exception)