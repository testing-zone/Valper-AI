"""Jira Cloud: pending issues assigned to the user (REST API + API token)."""
import httpx

from app.core.config import settings


async def jira_pending(jql: str = "") -> dict:
    if not settings.jira_enabled:
        return {"error": "Jira no está configurado (JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN en .env)."}
    async with httpx.AsyncClient(timeout=20, auth=(settings.JIRA_EMAIL, settings.JIRA_API_TOKEN)) as client:
        r = await client.post(f"{settings.JIRA_URL}/rest/api/3/search/jql", json={
            "jql": jql or settings.JIRA_JQL,
            "maxResults": 30,
            "fields": ["summary", "status", "priority", "duedate", "updated", "project"],
        })
        r.raise_for_status()
        issues = []
        for i in r.json().get("issues", []):
            f = i["fields"]
            issues.append({
                "key": i["key"],
                "summary": f.get("summary"),
                "status": (f.get("status") or {}).get("name"),
                "priority": (f.get("priority") or {}).get("name"),
                "due": f.get("duedate"),
                "project": (f.get("project") or {}).get("name"),
                "url": f"{settings.JIRA_URL}/browse/{i['key']}",
            })
    return {"issues": issues}


TOOLS = [
    {
        "name": "jira_pending",
        "description": "Tickets de Jira pendientes asignados al usuario (o un JQL propio).",
        "parameters": {"type": "object", "properties": {"jql": {"type": "string"}}},
        "handler": jira_pending,
    }
]
