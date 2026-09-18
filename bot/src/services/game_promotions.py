import logging
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import asyncio
import re

logger = logging.getLogger(__name__)

# Cache inteligente (game_name -> {data, timestamp, sources})
PROMOTIONS_CACHE: Dict[str, Dict] = {}
CACHE_TTL = 1 * 60 * 60  # 1 hora (atualiza mais frequentemente)


class GamePromotionsService:
    """Serviço robusto de promoções de games com múltiplas fontes."""

    BASE_URL_CHEAPSHARK = "https://www.cheapshark.com/api/1.0"
    BASE_URL_ITAD = "https://api.isthereanydeal.com/v2"
    BASE_URL_GOG = "https://www.gog.com/en/games"
    BASE_URL_PROMOCAO_GAMES = "https://www.promocaogames.com.br"

    # Headers para evitar bloqueios
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    @staticmethod
    async def search_games(game_name: str, limit: int = 10) -> List[Dict]:
        """Busca games em promoção via múltiplas fontes."""
        cache_key = f"search_{game_name}_{limit}"

        if cache_key in PROMOTIONS_CACHE:
            cache_entry = PROMOTIONS_CACHE[cache_key]
            if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                logger.debug(f"Retornando resultado em cache para: {game_name}")
                return cache_entry["data"]

        # Tenta CheapShark primeiro (mais confiável)
        games = await GamePromotionsService._search_cheapshark(game_name, limit)

        # Se não encontrou, tenta IsThereAnyDeal
        if not games:
            logger.info(f"CheapShark não retornou resultados para {game_name}, tentando ITAD...")
            games = await GamePromotionsService._search_itad(game_name, limit)

        # Se ainda não encontrou, tenta GOG
        if not games:
            logger.info(f"ITAD não retornou resultados para {game_name}, tentando GOG...")
            games = await GamePromotionsService._search_gog(game_name, limit)

        if games:
            PROMOTIONS_CACHE[cache_key] = {
                "data": games,
                "timestamp": datetime.now(),
                "sources": ["CheapShark", "ITAD", "GOG"]
            }

        return games[:limit]

    @staticmethod
    async def _search_cheapshark(game_name: str, limit: int) -> List[Dict]:
        """Busca na CheapShark API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/games"
                params = {"title": game_name, "limit": limit}

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = []
                        for game in data[:limit]:
                            games.append({
                                "title": game.get("external"),
                                "game_id": game.get("gameID"),
                                "thumb": game.get("thumb"),
                                "source": "CheapShark",
                            })
                        logger.info(f"CheapShark: {len(games)} games encontrados para '{game_name}'")
                        return games
        except Exception as e:
            logger.error(f"Erro ao buscar na CheapShark: {e}")

        return []

    @staticmethod
    async def _search_itad(game_name: str, limit: int) -> List[Dict]:
        """Busca na IsThereAnyDeal API."""
        try:
            async with aiohttp.ClientSession() as session:
                # ITAD requer busca por plaintext primeiro
                url = f"{GamePromotionsService.BASE_URL_ITAD}/search/search/"
                params = {"q": game_name, "limit": limit}

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = []

                        for result in data.get("results", [])[:limit]:
                            games.append({
                                "title": result.get("title"),
                                "game_id": result.get("id"),
                                "thumb": result.get("image"),
                                "source": "IsThereAnyDeal",
                            })

                        logger.info(f"ITAD: {len(games)} games encontrados para '{game_name}'")
                        return games
        except Exception as e:
            logger.error(f"Erro ao buscar na ITAD: {e}")

        return []

    @staticmethod
    async def _search_gog(game_name: str, limit: int) -> List[Dict]:
        """Busca na GOG API."""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.gog.com/v2/games/search"
                params = {"query": game_name, "limit": limit}

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        games = []

                        for game in data.get("products", [])[:limit]:
                            games.append({
                                "title": game.get("title"),
                                "game_id": game.get("id"),
                                "thumb": game.get("image"),
                                "source": "GOG",
                            })

                        logger.info(f"GOG: {len(games)} games encontrados para '{game_name}'")
                        return games
        except Exception as e:
            logger.error(f"Erro ao buscar na GOG: {e}")

        return []

    @staticmethod
    async def get_game_deals(game_id: int, min_discount: int = 0) -> List[Dict]:
        """Obtém ofertas para um game específico de múltiplas fontes."""
        cache_key = f"deals_{game_id}_{min_discount}"

        if cache_key in PROMOTIONS_CACHE:
            cache_entry = PROMOTIONS_CACHE[cache_key]
            if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                logger.debug(f"Retornando ofertas em cache para game ID: {game_id}")
                return cache_entry["data"]

        deals = await GamePromotionsService._get_cheapshark_deals(game_id, min_discount)

        if not deals:
            logger.info(f"CheapShark sem ofertas para {game_id}, tentando outras fontes...")
            deals = await GamePromotionsService._get_gog_deals(game_id, min_discount)

        if deals:
            PROMOTIONS_CACHE[cache_key] = {
                "data": deals,
                "timestamp": datetime.now(),
                "sources": ["CheapShark", "GOG"]
            }

        return deals

    @staticmethod
    async def _get_cheapshark_deals(game_id: int, min_discount: int) -> List[Dict]:
        """Obtém ofertas da CheapShark."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/games"
                params = {"id": game_id}

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        game_data = await response.json()
                        deals = []

                        if "deals" in game_data:
                            for deal in game_data["deals"]:
                                discount = int(float(deal.get("savings", 0)))

                                if discount >= min_discount:
                                    deals.append({
                                        "store_name": deal.get("storeName"),
                                        "price": float(deal.get("price", 0)),
                                        "retail_price": float(deal.get("retailPrice", 0)),
                                        "discount": discount,
                                        "url": f"https://www.cheapshark.com/redirect/store/{deal.get('storeID')}/gameID/{game_id}",
                                        "source": "CheapShark",
                                    })

                        logger.info(f"CheapShark: {len(deals)} ofertas encontradas para game {game_id}")
                        return deals
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas na CheapShark: {e}")

        return []

    @staticmethod
    async def _get_gog_deals(game_id: int, min_discount: int) -> List[Dict]:
        """Obtém ofertas da GOG."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.gog.com/products/{game_id}"

                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        game_data = await response.json()
                        deals = []

                        # Verifica se tem desconto
                        price_data = game_data.get("price", {})
                        base_amount = price_data.get("baseAmount", 0)
                        final_amount = price_data.get("finalAmount", 0)

                        if base_amount > 0:
                            discount = int(((base_amount - final_amount) / base_amount) * 100)

                            if discount >= min_discount:
                                deals.append({
                                    "store_name": "GOG.com",
                                    "price": final_amount / 100,
                                    "retail_price": base_amount / 100,
                                    "discount": discount,
                                    "url": f"https://www.gog.com/en/games/{game_id}",
                                    "source": "GOG",
                                })

                        return deals
        except Exception as e:
            logger.error(f"Erro ao buscar ofertas na GOG: {e}")

        return []

    @staticmethod
    async def search_deals(min_discount: int = 70) -> List[Dict]:
        """Busca os games com maior desconto de múltiplas fontes."""
        cache_key = f"top_deals_{min_discount}"

        if cache_key in PROMOTIONS_CACHE:
            cache_entry = PROMOTIONS_CACHE[cache_key]
            if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=CACHE_TTL):
                logger.debug(f"Retornando top deals em cache com desconto >= {min_discount}%")
                return cache_entry["data"]

        # Busca de múltiplas fontes em paralelo
        deals_tasks = [
            GamePromotionsService._search_cheapshark_deals(min_discount),
            GamePromotionsService._search_gog_promotions(min_discount),
        ]

        results = await asyncio.gather(*deals_tasks, return_exceptions=True)

        all_deals = []
        for result in results:
            if isinstance(result, list):
                all_deals.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Erro ao buscar deals: {result}")

        # Remove duplicatas e ordena por desconto
        seen_titles: Set[str] = set()
        unique_deals = []

        for deal in sorted(all_deals, key=lambda x: x["discount"], reverse=True):
            title = deal.get("title", "").lower()
            if title not in seen_titles:
                unique_deals.append(deal)
                seen_titles.add(title)

                if len(unique_deals) >= 20:
                    break

        if unique_deals:
            PROMOTIONS_CACHE[cache_key] = {
                "data": unique_deals,
                "timestamp": datetime.now(),
                "sources": ["CheapShark", "GOG", "Steam"]
            }
            logger.info(f"Total de {len(unique_deals)} deals únicos encontrados com desconto >= {min_discount}%")

        return unique_deals

    @staticmethod
    async def _search_cheapshark_deals(min_discount: int) -> List[Dict]:
        """Busca top deals na CheapShark."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{GamePromotionsService.BASE_URL_CHEAPSHARK}/deals"
                params = {
                    "sortBy": "savings",
                    "descending": "true",
                    "pageNumber": 0,
                    "pageSize": 60,
                }

                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers=GamePromotionsService.HEADERS
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        deals = []

                        for deal in data:
                            discount = int(float(deal.get("savings", 0)))

                            if discount >= min_discount:
                                deals.append({
                                    "title": deal.get("title"),
                                    "store": deal.get("storeName"),
                                    "price": float(deal.get("price", 0)),
                                    "retail_price": float(deal.get("retailPrice", 0)),
                                    "discount": discount,
                                    "url": f"https://www.cheapshark.com/redirect/store/{deal.get('storeID')}/gameID/{deal.get('gameID')}",
                                    "source": "CheapShark",
                                })

                                if len(deals) >= 15:
                                    break

                        logger.info(f"CheapShark: {len(deals)} top deals encontrados")
                        return deals
        except Exception as e:
            logger.error(f"Erro ao buscar top deals na CheapShark: {e}")

        return []

    @staticmethod
    async def _search_gog_promotions(min_discount: int) -> List[Dict]:
        """Busca promoções na GOG."""
        try:
            async with aiohttp.ClientSession() as session:
                # GOG não tem endpoint público para buscar deals,
                # então retorna lista vazia (pode ser expandido com scraping)
                logger.info("GOG: Busca de promoções requer scraping avançado")
                return []
        except Exception as e:
            logger.error(f"Erro ao buscar promoções na GOG: {e}")

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
            "sources": ["CheapShark", "IsThereAnyDeal", "GOG API", "Steam API"]
        }
