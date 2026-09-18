import pytest
import tempfile
import os
from bot.src.storage.database import Database


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db = Database(db_path=db_path)
    db.connect()
    yield db
    db.disconnect()
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


def test_database_connection(temp_db):
    """Test database connection."""
    assert temp_db.connection is not None


def test_save_and_get_welcome_message(temp_db):
    """Test saving and retrieving welcome message."""
    guild_id = 123456
    channel_id = 789012
    message = "Bem-vindo, {mention}!"

    success = temp_db.save_welcome_message(guild_id, channel_id, message)
    assert success is True

    retrieved = temp_db.get_welcome_message(guild_id)
    assert retrieved is not None
    assert retrieved["message"] == message
    assert retrieved["channel_id"] == channel_id


def test_welcome_history(temp_db):
    """Test welcome history tracking."""
    guild_id = 123456
    user_id = 789012
    username = "TestUser"

    # Save first entry
    temp_db.save_welcome_history(guild_id, user_id, username)

    # Get history
    history = temp_db.get_welcome_history(guild_id)
    assert len(history) > 0
    assert history[0]["user_id"] == user_id
    assert history[0]["username"] == username


def test_add_holiday(temp_db):
    """Test adding holidays."""
    date = "2024-12-25"
    name = "Natal"

    success = temp_db.add_holiday(date, name, country="BR")
    assert success is True

    holidays = temp_db.get_holidays(country="BR")
    holiday_dates = [h["date"] for h in holidays]
    assert date in holiday_dates


def test_notification_channels(temp_db):
    """Test setting and getting notification channels."""
    guild_id = 123456
    channel_id = 789012
    notif_type = "holidays"

    success = temp_db.set_notification_channel(guild_id, channel_id, notif_type)
    assert success is True

    retrieved = temp_db.get_notification_channel(guild_id, notif_type)
    assert retrieved == channel_id


def test_game_followers(temp_db):
    """Test adding and getting game followers."""
    user_id = 123456
    guild_id = 789012
    game_name = "Elden Ring"

    success = temp_db.add_game_follower(user_id, guild_id, game_name)
    assert success is True

    followers = temp_db.get_game_followers(game_name, guild_id)
    assert user_id in followers


def test_add_promotion(temp_db):
    """Test adding promotions."""
    game_name = "Elden Ring"
    store = "Steam"
    discount = 50
    sale_price = 150.00
    regular_price = 300.00
    url = "https://example.com"

    success = temp_db.add_promotion(
        game_name, store, discount, sale_price, regular_price, url
    )
    assert success is True

    promotions = temp_db.get_promotions(min_discount=50)
    assert len(promotions) > 0


def test_get_promotions_with_filter(temp_db):
    """Test filtering promotions by discount."""
    # Add two promotions
    temp_db.add_promotion("Game1", "Steam", 30, 70.0, 100.0, "url1")
    temp_db.add_promotion("Game2", "Epic", 80, 20.0, 100.0, "url2")

    # Get only 80% discount
    promotions = temp_db.get_promotions(min_discount=80)
    assert len(promotions) >= 1
    for promo in promotions:
        assert promo["discount_percentage"] >= 80


def test_database_unique_constraints(temp_db):
    """Test unique constraints."""
    # Test welcome message uniqueness
    temp_db.save_welcome_message(123, 456, "Message1")
    temp_db.save_welcome_message(123, 789, "Message2")  # Should replace

    welcome = temp_db.get_welcome_message(123)
    assert welcome["channel_id"] == 789  # Last one wins (OR REPLACE)

    # Test game follower uniqueness
    temp_db.add_game_follower(1, 2, "Game")
    temp_db.add_game_follower(1, 2, "Game")  # Duplicate

    followers = temp_db.get_game_followers("Game", 2)
    assert len(followers) == 1  # Only one entry


def test_database_query_methods(temp_db):
    """Test basic query methods."""
    # Test fetch_one
    temp_db.add_holiday("2024-01-01", "Ano Novo", "BR")
    result = temp_db.fetch_one(
        "SELECT * FROM holidays WHERE date = ?", ("2024-01-01",)
    )
    assert result is not None
    assert result["name"] == "Ano Novo"

    # Test fetch_all
    results = temp_db.fetch_all("SELECT * FROM holidays WHERE country = ?", ("BR",))
    assert isinstance(results, list)
