import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection: Optional[sqlite3.Connection] = None

    def connect(self):
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Conectado ao banco de dados: {self.db_path}")
            self._create_tables()
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def disconnect(self):
        if self.connection:
            self.connection.close()
            logger.info("Desconectado do banco de dados")

    def _create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS welcome_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS welcome_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                username TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                country TEXT DEFAULT 'BR',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, country)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS holiday_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                days_before INTEGER DEFAULT 3,
                enabled BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, type)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_followers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                game_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, guild_id, game_name)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_name TEXT NOT NULL,
                store TEXT NOT NULL,
                discount_percentage INTEGER NOT NULL,
                sale_price REAL NOT NULL,
                regular_price REAL NOT NULL,
                url TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                UNIQUE(game_name, store, sale_price)
            )
            """
        )

        self.connection.commit()
        logger.info("Tabelas do banco de dados criadas/verificadas com sucesso")

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        return cursor

    def execute_many(self, query: str, params_list: List[tuple]):
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        self.connection.commit()

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def save_welcome_message(self, guild_id: int, channel_id: int, message: str) -> bool:
        try:
            cursor = self.execute(
                """
                INSERT OR REPLACE INTO welcome_messages (guild_id, channel_id, message, enabled)
                VALUES (?, ?, ?, 1)
                """,
                (guild_id, channel_id, message),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar mensagem de boas-vindas: {e}")
            return False

    def get_welcome_message(self, guild_id: int) -> Optional[Dict[str, Any]]:
        return self.fetch_one(
            "SELECT * FROM welcome_messages WHERE guild_id = ? AND enabled = 1", (guild_id,)
        )

    def save_welcome_history(self, guild_id: int, user_id: int, username: str) -> bool:
        try:
            self.execute(
                """
                INSERT INTO welcome_history (guild_id, user_id, username)
                VALUES (?, ?, ?)
                """,
                (guild_id, user_id, username),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao salvar histórico de boas-vindas: {e}")
            return False

    def get_welcome_history(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM welcome_history
            WHERE guild_id = ?
            ORDER BY sent_at DESC
            LIMIT ?
            """,
            (guild_id, limit),
        )

    def add_holiday(self, date: str, name: str, country: str = "BR") -> bool:
        try:
            self.execute(
                """
                INSERT OR IGNORE INTO holidays (date, name, country)
                VALUES (?, ?, ?)
                """,
                (date, name, country),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar feriado: {e}")
            return False

    def get_holidays(self, country: str = "BR") -> List[Dict[str, Any]]:
        return self.fetch_all("SELECT * FROM holidays WHERE country = ? ORDER BY date", (country,))

    def set_notification_channel(self, guild_id: int, channel_id: int, notification_type: str) -> bool:
        try:
            self.execute(
                """
                INSERT OR REPLACE INTO notification_channels (guild_id, channel_id, type)
                VALUES (?, ?, ?)
                """,
                (guild_id, channel_id, notification_type),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao definir canal de notificações: {e}")
            return False

    def get_notification_channel(self, guild_id: int, notification_type: str) -> Optional[int]:
        result = self.fetch_one(
            "SELECT channel_id FROM notification_channels WHERE guild_id = ? AND type = ?",
            (guild_id, notification_type),
        )
        return result["channel_id"] if result else None

    def add_game_follower(self, user_id: int, guild_id: int, game_name: str) -> bool:
        try:
            self.execute(
                """
                INSERT OR IGNORE INTO game_followers (user_id, guild_id, game_name)
                VALUES (?, ?, ?)
                """,
                (user_id, guild_id, game_name),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar seguidor de game: {e}")
            return False

    def get_game_followers(self, game_name: str, guild_id: int) -> List[int]:
        results = self.fetch_all(
            "SELECT user_id FROM game_followers WHERE game_name = ? AND guild_id = ?",
            (game_name, guild_id),
        )
        return [r["user_id"] for r in results]

    def add_promotion(
        self,
        game_name: str,
        store: str,
        discount_percentage: int,
        sale_price: float,
        regular_price: float,
        url: str,
        expires_at: Optional[str] = None,
    ) -> bool:
        try:
            self.execute(
                """
                INSERT OR IGNORE INTO promotions (game_name, store, discount_percentage, sale_price, regular_price, url, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (game_name, store, discount_percentage, sale_price, regular_price, url, expires_at),
            )
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar promoção: {e}")
            return False

    def get_promotions(self, min_discount: int = 0) -> List[Dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM promotions
            WHERE discount_percentage >= ? AND (expires_at IS NULL OR expires_at > datetime('now'))
            ORDER BY discount_percentage DESC
            LIMIT 50
            """,
            (min_discount,),
        )
