# Caminho: bot/src/bot.py

import logging
import discord # <-- ADICIONE ESTA LINHA

from bot.src import settings
from bot.src.core.client import MusicBot

_logger = logging.getLogger(__name__)

def main():
    """Função principal para iniciar o bot."""
    settings.setup_logging()
    
    _logger.info("Iniciando o Music Bot...")
    
    if not settings.TOKEN:
        _logger.critical("O DISCORD_TOKEN não foi encontrado. Verifique seu arquivo .env.")
        return

    bot = MusicBot(guild_ids=settings.GUILD_IDS)
    
    try:
        bot.run(settings.TOKEN)
    except discord.LoginFailure:
        _logger.critical("Falha no login. Token inválido.")
    except Exception as e:
        _logger.critical(f"Erro inesperado ao iniciar o bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()