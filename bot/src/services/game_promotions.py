import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio

logger = logging.getLogger(__name__)

# Cache simples (game_name -> {data, timestamp})
PROMOTIONS_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 2 * 60 * 60  # 2 horas


class GamePromotionsService:
    BASE_URL_CHEAPSHARK = "https://www.cheapshark.com/api/1.0"
    BASE_URL_ITAD = "https://api.isthereanydeal.com"

    @staticmethod
    async def search_games(game_name: str, limit: int = 10) -> List[Dict]:
        """Busca games em promoção via CheapShark API."""
        try:
            # Check cache first
            cache_key = f"search_{game_name}_{limit}"
            if cache_key in PROMOTIONS_CACHE:
                cache_entry = PROMOTIONS_CACHE[cache_key]
                if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                    logger.debug(f"Retornando resultado em cache para: {game_name}")
                    return cache_entry["data"]

            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/games"
                params = {"title": game_name, "limit": limit}

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Format results
                        games = []
                        for game in data:
                            games.append(
                                {
                                    "title": game.get("external"),
                                    "game_id": game.get("gameID"),
                                    "thumb": game.get("thumb"),
                                }
                            )

                        # Cache result
                        PROMOTIONS_CACHE[cache_key] = {
                            "data": games,
                            "timestamp": datetime.now(),
                        }

                        return games[:limit]
                    else:
                        logger.warning(f"CheapShark API retornou status {response.status}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"Timeout ao buscar games: {game_name}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar games: {e}")
            return []

    @staticmethod
    async def get_game_deals(game_id: int, min_discount: int = 0) -> List[Dict]:
        """Obtém ofertas para um game específico."""
        try:
            cache_key = f"deals_{game_id}_{min_discount}"
            if cache_key in PROMOTIONS_CACHE:
                cache_entry = PROMOTIONS_CACHE[cache_key]
                if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                    logger.debug(f"Retornando ofertas em cache para game ID: {game_id}")
                    return cache_entry["data"]

            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/games"
                params = {"id": game_id}

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        game_data = await response.json()

                        deals = []
                        if "deals" in game_data:
                            for deal in game_data["deals"]:
                                discount = int(float(deal.get("savings", 0)))

                                if discount >= min_discount:
                                    deals.append(
                                        {
                                            "store_name": deal.get("storeName"),
                                            "price": float(deal.get("price", 0)),
                                            "retail_price": float(deal.get("retailPrice", 0)),
                                            "discount": discount,
                                            "url": f"https://www.cheapshark.com/redirect/store/{deal.get('storeID')}/gameID/{game_id}",
                                            "last_change": deal.get("lastChange"),
                                        }
                                    )

                        # Cache result
                        PROMOTIONS_CACHE[cache_key] = {
                            "data": deals,
                            "timestamp": datetime.now(),
                        }

                        return deals
                    else:
                        logger.warning(f"CheapShark API retornou status {response.status}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"Timeout ao buscar ofertas para game ID: {game_id}")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas: {e}")
            return []

    @staticmethod
    async def search_deals(min_discount: int = 70) -> List[Dict]:
        """Busca os games com maior desconto."""
        try:
            cache_key = f"top_deals_{min_discount}"
            if cache_key in PROMOTIONS_CACHE:
                cache_entry = PROMOTIONS_CACHE[cache_key]
                if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                    logger.debug(f"Retornando top deals em cache com desconto >= {min_discount}%")
                    return cache_entry["data"]

            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/deals"
                params = {
                    "sortBy": "savings",
                    "descending": "true",
                    "pageNumber": 0,
                    "pageSize": 60,
                }

                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()

                        deals = []
                        for deal in data:
                            discount = int(float(deal.get("savings", 0)))

                            if discount >= min_discount:
                                deals.append(
                                    {
                                        "title": deal.get("title"),
                                        "store": deal.get("storeName"),
                                        "price": float(deal.get("price", 0)),
                                        "retail_price": float(deal.get("retailPrice", 0)),
                                        "discount": discount,
                                        "game_id": deal.get("gameID"),
                                        "url": f"https://www.cheapshark.com/redirect/store/{deal.get('storeID')}/gameID/{deal.get('gameID')}",
                                        "thumb": deal.get("thumb"),
                                    }
                                )

                                if len(deals) >= 20:
                                    break

                        # Cache result
                        PROMOTIONS_CACHE[cache_key] = {
                            "data": deals,
                            "timestamp": datetime.now(),
                        }

                        return deals
                    else:
                        logger.warning(f"CheapShark API retornou status {response.status}")
                        return []

        except asyncio.TimeoutError:
            logger.error(f"Timeout ao buscar top deals com desconto >= {min_discount}%")
            return []
        except Exception as e:
            logger.error(f"Erro ao buscar top deals: {e}")
            return []

    @staticmethod
    def clear_cache():
        """Limpa o cache de promoções."""
        PROMOTIONS_CACHE.clear()
        logger.info("Cache de promoções limpo")

    @staticmethod
    def get_cache_info() -> Dict:
        """Retorna informações sobre o cache."""
        return {
            "size": len(PROMOTIONS_CACHE),
            "ttl_hours": CACHE_TTL / 3600,
            "entries": list(PROMOTIONS_CACHE.keys())[:10],
        }
