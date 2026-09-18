import pytest
import asyncio
from bot.src.services.game_promotions import GamePromotionsService


@pytest.mark.asyncio
async def test_search_games_returns_list():
    """Test that search_games returns a list."""
    result = await GamePromotionsService.search_games("Elden")
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_search_games_limit():
    """Test that search_games respects limit."""
    result = await GamePromotionsService.search_games("a", limit=5)
    assert len(result) <= 5


@pytest.mark.asyncio
async def test_search_games_empty_name():
    """Test search with empty game name."""
    result = await GamePromotionsService.search_games("")
    # Should return list (empty or with results)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_search_deals_returns_list():
    """Test that search_deals returns a list."""
    result = await GamePromotionsService.search_deals(min_discount=70)
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_search_deals_discount_filter():
    """Test that deals have at least the minimum discount."""
    result = await GamePromotionsService.search_deals(min_discount=50)
    for deal in result:
        assert deal["discount"] >= 50


@pytest.mark.asyncio
async def test_search_deals_limit():
    """Test that results are reasonable."""
    result = await GamePromotionsService.search_deals(min_discount=80)
    # Should not have thousands of deals
    assert len(result) <= 100


def test_cache_operations():
    """Test cache management."""
    info_before = GamePromotionsService.get_cache_info()
    assert "size" in info_before
    assert "ttl_hours" in info_before

    # Clear cache
    GamePromotionsService.clear_cache()
    info_after = GamePromotionsService.get_cache_info()
    assert info_after["size"] == 0


@pytest.mark.asyncio
async def test_search_games_caching():
    """Test that consecutive searches use cache."""
    # First search
    result1 = await GamePromotionsService.search_games("test", limit=5)
    info1 = GamePromotionsService.get_cache_info()

    # Second search (should be cached)
    result2 = await GamePromotionsService.search_games("test", limit=5)
    info2 = GamePromotionsService.get_cache_info()

    # Results should be identical
    if result1 and result2:
        assert result1 == result2
        # Cache should have entries
        assert info2["size"] > 0
