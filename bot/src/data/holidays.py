from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Feriados brasileiros fixos (mês, dia)
FIXED_HOLIDAYS = [
    (1, 1, "Ano Novo"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Consciência Negra"),
    (12, 25, "Natal"),
]

# Feriados Municipais - Imperatriz/MA
IMPERATRIZ_MUNICIPAL_HOLIDAYS = [
    (10, 28, "Aniversário de Imperatriz"),  # Feriado municipal mais importante
    (6, 23, "Santo Antônio"),  # Celebração local
]

# Feriados Estaduais - Maranhão
MARANHAO_STATE_HOLIDAYS = [
    (6, 23, "Santo Antônio"),
    (10, 28, "Zumbi dos Palmares"),  # Alguns estados do nordeste celebram
]


def easter_date(year: int) -> Tuple[int, int]:
    """Calcula a data da Páscoa para um determinado ano usando o algoritmo de Meeus."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return month, day


def get_movable_holidays(year: int) -> List[Dict[str, any]]:
    """Retorna feriados móveis para um determinado ano."""
    month, day = easter_date(year)
    easter = datetime(year, month, day)

    movable = [
        {
            "date": (easter - timedelta(days=47)).strftime("%Y-%m-%d"),
            "name": "Sexta-feira da Paixão (segunda antes do Carnaval)",
        },
        {
            "date": (easter - timedelta(days=48)).strftime("%Y-%m-%d"),
            "name": "Carnaval (sábado)",
        },
        {
            "date": (easter - timedelta(days=47)).strftime("%Y-%m-%d"),
            "name": "Carnaval (segunda)",
        },
        {
            "date": (easter - timedelta(days=2)).strftime("%Y-%m-%d"),
            "name": "Sexta-feira Santa",
        },
        {
            "date": (easter + timedelta(days=60)).strftime("%Y-%m-%d"),
            "name": "Corpus Christi",
        },
    ]

    return movable


def get_all_holidays(year: int, include_municipal: bool = False, city: str = "Imperatriz") -> List[Dict[str, any]]:
    """Retorna todos os feriados (fixos e móveis) para um determinado ano.

    Args:
        year: Ano a buscar os feriados
        include_municipal: Se True, inclui feriados municipais
        city: Cidade para buscar feriados municipais (padrão: Imperatriz)
    """
    holidays = []

    # Feriados fixos nacionais
    for month, day, name in FIXED_HOLIDAYS:
        holidays.append(
            {
                "date": f"{year:04d}-{month:02d}-{day:02d}",
                "name": name,
                "type": "fixed",
                "scope": "nacional",
            }
        )

    # Feriados móveis nacionais
    movable = get_movable_holidays(year)
    for holiday in movable:
        holidays.append(
            {
                "date": holiday["date"],
                "name": holiday["name"],
                "type": "movable",
                "scope": "nacional",
            }
        )

    # Feriados municipais (opcional)
    if include_municipal:
        if city.lower() == "imperatriz":
            for month, day, name in IMPERATRIZ_MUNICIPAL_HOLIDAYS:
                holidays.append(
                    {
                        "date": f"{year:04d}-{month:02d}-{day:02d}",
                        "name": f"{name} 🏙️",
                        "type": "fixed",
                        "scope": "municipal",
                    }
                )

    return sorted(holidays, key=lambda h: h["date"])


def get_upcoming_holidays(days_before: int = 3, include_municipal: bool = False, city: str = "Imperatriz") -> List[Dict[str, any]]:
    """Retorna feriados próximos com antecedência especificada."""
    today = datetime.now()
    upcoming = []

    # Busca feriados nos próximos 2 anos (para cobrir feriados do próximo ano)
    for year in [today.year, today.year + 1]:
        holidays = get_all_holidays(year, include_municipal=include_municipal, city=city)

        for holiday in holidays:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")

            # Verifica se o feriado está dentro da janela de antecedência
            if today <= holiday_date <= today + timedelta(days=days_before):
                days_until = (holiday_date - today).days
                upcoming.append(
                    {
                        **holiday,
                        "days_until": days_until,
                    }
                )

    return sorted(upcoming, key=lambda h: h["date"])


def get_next_holidays(limit: int = 5, include_municipal: bool = False, city: str = "Imperatriz") -> List[Dict[str, any]]:
    """Retorna os próximos N feriados."""
    today = datetime.now()
    holidays_list = []

    for year in [today.year, today.year + 1]:
        holidays = get_all_holidays(year, include_municipal=include_municipal, city=city)

        for holiday in holidays:
            holiday_date = datetime.strptime(holiday["date"], "%Y-%m-%d")

            if holiday_date >= today:
                days_until = (holiday_date - today).days
                holidays_list.append(
                    {
                        **holiday,
                        "days_until": days_until,
                    }
                )

                if len(holidays_list) >= limit:
                    return holidays_list[:limit]

    return holidays_list[:limit]


def is_holiday_today(include_municipal: bool = False, city: str = "Imperatriz") -> Dict[str, any] | None:
    """Verifica se hoje é feriado."""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    holidays = get_all_holidays(today.year, include_municipal=include_municipal, city=city)

    for holiday in holidays:
        if holiday["date"] == today_str:
            return holiday

    return None


def get_holiday_by_date(date_str: str) -> Dict[str, any] | None:
    """Busca um feriado por data (formato: YYYY-MM-DD)."""
    year = int(date_str[:4])
    holidays = get_all_holidays(year)

    for holiday in holidays:
        if holiday["date"] == date_str:
            return holiday

    return None
