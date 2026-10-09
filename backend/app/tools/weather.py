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
                try:  # Open-Meteo has intermittent 5xx; fall back to MET Norway
                    out[name] = await _fetch_met_no(client, lat, lon)
                except Exception as e2:
                    out[name] = {"error": f"{str(e)[:120]} / met.no: {str(e2)[:80]}"}
    return out


async def _fetch_city(client: httpx.AsyncClient, lat: float, lon: float, attempts: int = 3) -> dict:
    for attempt in range(attempts):
        try:
            r = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon, "timezone": settings.TIMEZONE, "forecast_days": 2,
                "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,precipitation",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
                "hourly": "temperature_2m,precipitation_probability,weather_code",
            })
            r.raise_for_status()
            break
        except httpx.HTTPError:
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(3 * (attempt + 1))
    d = r.json()
    cur, day = d["current"], d["daily"]
    rest = _rest_of_day(d.get("hourly") or {}, cur["time"])
    return {
        "resto_del_dia": rest,
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


def _rest_of_day(hourly: dict, now_iso: str) -> str:
    """'tarde: 24–28°C, lluvia 80% (15–17h); noche: 21–23°C, lluvia 40%' from the hourly forecast."""
    if not hourly.get("time"):
        return ""
    today, now_h = now_iso[:10], int(now_iso[11:13])
    blocks = [("mañana", 6, 12), ("tarde", 12, 18), ("noche", 18, 24)]
    parts = []
    for name, start, end in blocks:
        if end <= now_h:
            continue
        rows = [(int(t[11:13]), temp, prob, code) for t, temp, prob, code in
                zip(hourly["time"], hourly["temperature_2m"], hourly["precipitation_probability"], hourly["weather_code"])
                if t.startswith(today) and max(start, now_h) <= int(t[11:13]) < end]
        if not rows:
            continue
        temps = [r[1] for r in rows]
        probs = [r[2] or 0 for r in rows]
        top = max(probs)
        rainy = [r[0] for r in rows if (r[2] or 0) >= max(50, top - 10)]
        window = f" ({min(rainy)}–{max(rainy) + 1}h)" if rainy and top >= 40 else ""
        worst = max(rows, key=lambda r: r[3])[3]
        parts.append(f"{name}: {min(temps):.0f}–{max(temps):.0f}°C, {WMO.get(worst, 'variable')}, "
                     f"lluvia {top}%{window}")
    return "; ".join(parts)


MET_SYMBOLS = {"clearsky": "despejado", "fair": "mayormente despejado", "partlycloudy": "parcialmente nublado",
               "cloudy": "nublado", "fog": "niebla", "lightrain": "lluvia ligera", "rain": "lluvia",
               "heavyrain": "lluvia fuerte", "lightrainshowers": "chubascos ligeros", "rainshowers": "chubascos",
               "heavyrainshowers": "chubascos fuertes", "rainandthunder": "tormenta",
               "rainshowersandthunder": "chubascos con tormenta"}


async def _fetch_met_no(client: httpx.AsyncClient, lat: float, lon: float) -> dict:
    """Backup provider: MET Norway locationforecast (free, requires an identifying User-Agent)."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    r = await client.get("https://api.met.no/weatherapi/locationforecast/2.0/compact",
                         params={"lat": round(lat, 4), "lon": round(lon, 4)},
                         headers={"User-Agent": "personal-assistant/1.0 github.com/testing-zone/Valper-AI"})
    r.raise_for_status()
    series = r.json()["properties"]["timeseries"]
    tz = ZoneInfo(settings.TIMEZONE)
    now = series[0]
    symbol = (now["data"].get("next_1_hours") or now["data"].get("next_6_hours") or {}).get("summary", {}) \
        .get("symbol_code", "").split("_")[0]
    today = datetime.now(tz).date()

    def day_stats(day):
        temps, rain = [], 0.0
        for p in series:
            t = datetime.fromisoformat(p["time"].replace("Z", "+00:00")).astimezone(tz)
            if t.date() == day:
                temps.append(p["data"]["instant"]["details"]["air_temperature"])
                rain += (p["data"].get("next_1_hours") or {}).get("details", {}).get("precipitation_amount", 0)
        return (min(temps), max(temps), round(rain, 1)) if temps else (None, None, 0)

    tmin, tmax, rain = day_stats(today)
    t2min, t2max, rain2 = day_stats(today + timedelta(days=1))
    details = now["data"]["instant"]["details"]
    return {
        "temperatura": details["air_temperature"],
        "sensacion": details["air_temperature"],
        "humedad": details.get("relative_humidity"),
        "estado": MET_SYMBOLS.get(symbol, symbol or "—"),
        "max_hoy": tmax, "min_hoy": tmin,
        "prob_lluvia_hoy": f"{rain} mm",
        "manana": f"{t2min}–{t2max}°C, lluvia {rain2} mm",
        "fuente": "met.no",
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
            f"lluvia {w['prob_lluvia_hoy']}{'' if 'mm' in str(w['prob_lluvia_hoy']) else '%'}."
            + (f" Resto del día — {w['resto_del_dia']}." if w.get("resto_del_dia") else "")
            + f" Mañana {w['manana']}."
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
