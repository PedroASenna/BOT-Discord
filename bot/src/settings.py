import os
from logging import config as logging_config

from dotenv import load_dotenv

load_dotenv()

# Discord Bot Token
TOKEN = os.getenv("DISCORD_TOKEN")

# Optional: Guild IDs for instant command sync
GUILD_IDS_STR = os.getenv("GUILD_IDS")
GUILD_IDS = [int(gid) for gid in GUILD_IDS_STR.split(",")] if GUILD_IDS_STR else None

# Lavalink Configuration
LAVALINK_HOST = os.getenv("LAVALINK_HOST", "localhost")
LAVALINK_PORT = int(os.getenv("LAVALINK_PORT", 2333))
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "youshallnotpass")
LAVALINK_URI = f"http://{LAVALINK_HOST}:{LAVALINK_PORT}"

# Logging Configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/bot.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
}

def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging_config.dictConfig(LOGGING_CONFIG)