"""Weather from Open-Meteo (free, no API key)."""
import asyncio

import httpx

from app.core.config import settings

WMO = {
    0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado", 3: "nublado",
    45: "niebla", 48: "niebla con escarcha", 51: "llovizna ligera", 53: "llovizna",
    55: "llovizna intensa", 61: "lluvia ligera", 63: "lluvia", 65: "lluvia fuerte",
    80: "chubascos ligeros", 81: "chubascos", 82: "chubascos fuertes",
    95: "tormenta", 96: "tormenta con granizo", 99: "tormenta fuerte con granizo",
}


async def get_weather(city: str = "") -> dict:
    """Current weather + today's forecast for one configured city, or all of them."""
    cities = settings.LOCATIONS
    if city:
        match = next((c for c in cities if c.lower().startswith(city.lower()[:4])), None)
        if not match:
            return {"error": f"Ciudad no configurada. Disponibles: {', '.join(cities)}"}
        cities = {match: cities[match]}

    out = {}
    async with httpx.AsyncClient(timeout=15) as client:
        for name, (lat, lon) in cities.items():
            try:
                out[name] = await _fetch_city(client, lat, lon)
            except Exception as e:
                out[name] = {"error": str(e)[:200]}
    return out


async def _fetch_city(client: httpx.AsyncClient, lat: float, lon: float, attempts: int = 3) -> dict:
    for attempt in range(attempts):
        try:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon, "timezone": settings.TIMEZONE, "forecast_days": 2,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
            })
            r.raise_for_status()
            break
        except httpx.HTTPError:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(3 * (attempt + 1))
    d = r.json()
    cur, day = d["current"], d["daily"]
    return {
        "temperatura": cur["temperature_2m"],
        "sensacion": cur["apparent_temperature"],
        "humedad": cur["relative_humidity_2m"],
        "estado": WMO.get(cur["weather_code"], f"código {cur['weather_code']}"),
        "max_hoy": day["temperature_2m_max"][0],
        "min_hoy": day["temperature_2m_min"][0],
        "prob_lluvia_hoy": day["precipitation_probability_max"][0],
        "manana": f"{day['temperature_2m_min'][1]}–{day['temperature_2m_max'][1]}°C, "
                  f"{WMO.get(day['weather_code'][1], '')}, lluvia {day['precipitation_probability_max'][1]}%",
    }


def format_weather(data: dict) -> str:
    lines = []
    for name, w in data.items():
        if "error" in w:
            lines.append(f"**{name}**: no disponible ahora.")
            continue
        lines.append(
            f"**{name}**: {w['temperatura']}°C ({w['estado']}), sensación {w['sensacion']}°C, "
            f"humedad {w['humedad']}%. Hoy {w['min_hoy']}–{w['max_hoy']}°C, "
            f"lluvia {w['prob_lluvia_hoy']}%. Mañana {w['manana']}."
        )
    return "\n".join(lines)


TOOLS = [
    {
        "name": "get_weather",
        "description": f"Clima actual y pronóstico (hoy y mañana) para: {', '.join(settings.LOCATIONS)}.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "Una de las ciudades. Vacío = todas."}},
        },
        "handler": get_weather,
    }
]
