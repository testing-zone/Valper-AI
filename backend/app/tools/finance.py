"""USD exchange rate for CURRENCY. For COP also the official TRM (Banco de la República)."""
import httpx

from app.core.config import settings


async def get_dollar() -> dict:
    out = {"moneda": settings.CURRENCY}
    async with httpx.AsyncClient(timeout=15) as client:
        if settings.CURRENCY.upper() == "COP":
            await _trm(client, out)
        try:
            r = await client.get("https://open.er-api.com/v6/latest/USD")
            out["mercado"] = round(r.json()["rates"][settings.CURRENCY.upper()], 2)
        except Exception as e:
            out["mercado_error"] = str(e)[:120]
    return out


async def _trm(client: httpx.AsyncClient, out: dict):
    try:
        r = await client.get("https://www.datos.gov.co/resource/32sa-8pi3.json",
                             params={"$order": "vigenciadesde DESC", "$limit": 2})
        rows = r.json()
        out["trm_hoy"] = float(rows[0]["valor"])
        out["trm_fecha"] = rows[0]["vigenciadesde"][:10]
        if len(rows) > 1:
            out["trm_anterior"] = float(rows[1]["valor"])
            out["variacion"] = round(out["trm_hoy"] - out["trm_anterior"], 2)
    except Exception as e:
        out["trm_error"] = str(e)[:120]


def format_dollar(d: dict) -> str:
    if "trm_hoy" not in d:
        return f"USD→{d.get('moneda')}: {d['mercado']:,.2f}" if "mercado" in d else "Dólar: sin datos."
    var = d.get("variacion")
    arrow = "" if var is None else f" ({'+' if var >= 0 else ''}{var:,.0f} vs ayer)"
    market = f" · mercado ~${d['mercado']:,.0f}" if "mercado" in d else ""
    return f"TRM ${d['trm_hoy']:,.2f}{arrow}{market}"


TOOLS = [
    {
        "name": "get_dollar",
        "description": "Precio del dólar en la moneda local (con TRM oficial si es COP) y variación.",
        "parameters": {"type": "object", "properties": {}},
        "handler": get_dollar,
    }
]
