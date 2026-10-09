"""Orca (Stably AI) integration — read-only for now: what are my coding agents doing?

Uses the `orca` CLI that ships inside Orca.app; every command supports --json.
Orca must be open (or `orca serve` running) for the runtime to answer.
"""
import asyncio
import json
import logging
import shutil

from app.core.config import settings

logger = logging.getLogger(__name__)

APP_CLI = "/Applications/Orca.app/Contents/Resources/bin/orca"


def cli() -> str:
    # prefer the CLI inside the app bundle: the /usr/local/bin/orca symlink can be broken after updates
    if settings.ORCA_BIN:
        return settings.ORCA_BIN
    import os
    return APP_CLI if os.path.exists(APP_CLI) else (shutil.which("orca") or APP_CLI)


def available() -> bool:
    return bool(shutil.which(cli()))


async def run(*args: str, timeout: int = 20):
    """Run an orca command with --json. Returns parsed JSON, or {"text": ...} if not JSON."""
    proc = await asyncio.create_subprocess_exec(
        cli(), *args, "--json", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise RuntimeError(f"orca {' '.join(args)}: sin respuesta en {timeout}s")
    text = out.decode(errors="ignore").strip()
    if proc.returncode != 0 and not text:
        raise RuntimeError(err.decode(errors="ignore").strip()[-400:] or f"exit {proc.returncode}")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"text": text[-4000:]}
    # every orca command answers {"id", "ok", "result": {...}}
    if isinstance(data, dict) and "result" in data:
        if data.get("ok") is False:
            raise RuntimeError(str(data.get("error"))[:400])
        return data["result"]
    return data


async def is_running() -> bool:
    try:
        status = await run("status", timeout=10)
    except Exception:
        return False
    if not isinstance(status, dict):
        return False
    return bool((status.get("runtime") or {}).get("reachable") or status.get("runtimeReachable"))


async def orca_agents(limit: int = 20) -> dict:
    """Snapshot of Orca worktrees and their agents, for the model to summarize."""
    if not available():
        return {"error": "No encuentro el CLI de Orca. ¿Está instalado Orca.app?"}
    if not await is_running():
        return {"error": "Orca está cerrado. Ábrelo (o corre `orca serve`) para ver los agentes."}
    data = {}
    try:
        data["worktrees"] = await run("worktree", "ps", "--limit", str(limit))
    except Exception as e:
        data["worktrees_error"] = str(e)
    try:
        data["terminals"] = await run("terminal", "list", "--limit", str(limit))
    except Exception as e:
        data["terminals_error"] = str(e)
    return data


async def orca_terminal_output(terminal: str, lines: int = 60) -> dict:
    """Last rendered screen of one agent terminal, to see what it is doing or asking."""
    if not await is_running():
        return {"error": "Orca está cerrado."}
    return await run("terminal", "read", "--terminal", terminal, "--screen", "--limit", str(lines * 200))


TOOLS = [
    {
        "name": "orca_agents",
        "description": "Estado de los agentes de código en Orca (worktrees, terminales, qué está haciendo cada "
                       "agente, cuáles terminaron o esperan respuesta). Úsalo para '¿qué están haciendo mis "
                       "agentes?', '¿ya terminó X?'. Resume en una línea por agente.",
        "parameters": {"type": "object", "properties": {}},
        "handler": orca_agents,
    },
    {
        "name": "orca_terminal_output",
        "description": "Lee la pantalla actual de la terminal de un agente en Orca (por su handle, de orca_agents) "
                       "para ver en qué va o qué está preguntando.",
        "parameters": {"type": "object", "properties": {"terminal": {"type": "string"}},
                       "required": ["terminal"]},
        "handler": orca_terminal_output,
    },
]


# ---- watcher: alert when an agent finishes, needs you, or fails ---------------

NEEDS_YOU = ("blocked", "waiting", "permission", "awaiting")
FINISHED = ("done", "idle")
FAILED = ("error", "failed", "interrupted")
REMIND_AFTER = 15 * 60

_last: dict = {}  # paneKey -> (kind, since_ts, reminded, episode)
_primed = False


def _kind(state: str) -> str:
    s = (state or "").lower()
    if any(k in s for k in NEEDS_YOU):
        return "needs_you"
    if any(k in s for k in FAILED):
        return "failed"
    if any(k in s for k in FINISHED):
        return "finished"
    return "working"


def _where(w: dict) -> str:
    name = w.get("displayName") or w.get("branch", "").replace("refs/heads/", "")
    return f"{w.get('repo')}/{name}" if name and name != w.get("repo", "").lower() else str(w.get("repo"))


async def watch():
    """Scheduler job. First run only records current states, so old agents don't spam."""
    global _primed
    import time
    from app.core import db

    if not available() or not await is_running():
        return
    try:
        data = await run("worktree", "ps", "--limit", "50")
    except Exception as e:
        logger.debug(f"orca watch failed: {e}")
        return
    en = db.language() == "en"
    title_word = f"{settings.USER_TITLE}, " if settings.USER_TITLE else ""
    now = time.time()
    seen = set()
    for w in data.get("worktrees", []):
        preview = w.get("preview") or ""
        if not w.get("agents") and "Enter to confirm" in preview:
            # e.g. Claude's trust/bypass screens: Orca doesn't list the agent yet
            key = f"screen:{w.get('worktreeId')}"
            seen.add(key)
            if key not in _last:
                _last[key] = ("needs_you", now, False, None)
                if _primed:
                    await _alert("needs_you", w, {"agentType": "claude", "prompt": ""}, en, title_word)
            continue
        for a in w.get("agents") or []:
            key = a.get("paneKey") or f"{w.get('worktreeId')}:{a.get('agentType')}"
            seen.add(key)
            kind = _kind(a.get("state"))
            # stateStartedAt changes on every new episode, so a task that went working -> done
            # between two polls still counts as a new completion
            episode = a.get("stateStartedAt") or (a.get("mainAgent") or {}).get("stateStartedAt")
            prev = _last.get(key)
            if prev and prev[0] == kind and prev[3] == episode:
                if kind == "needs_you" and not prev[2] and now - prev[1] > REMIND_AFTER:
                    _last[key] = (kind, prev[1], True, episode)
                    await _alert("needs_you", w, a, en, title_word, reminder=True)
                continue
            _last[key] = (kind, now, False, episode)
            if _primed and kind != "working":
                await _alert(kind, w, a, en, title_word)
    for key in list(_last):
        if key not in seen:
            _last.pop(key)
    _primed = True


async def _alert(kind: str, w: dict, a: dict, en: bool, title_word: str, reminder: bool = False):
    from app.core import db
    from app.tools import notify
    where = _where(w)
    task = (a.get("prompt") or a.get("taskTitle") or "").strip().replace("\n", " ")[:140]
    agent = a.get("agentType") or "agent"
    if kind == "finished":
        title = f"Orca · {agent} " + db.t(f"terminó en {where}", f"finished in {where}")
        result = (a.get("lastAssistantMessage") or "").strip()[:900]
        body = f"**{db.t('Tarea', 'Task')}:** {task}\n\n{result}" if task else result
        speak = (f"{title_word}the {agent} agent in {where} has finished." if en
                 else f"{title_word}el agente de {where} terminó.")
    elif kind == "needs_you":
        title = (f"Orca · {agent} " + db.t(f"te necesita en {where}", f"needs you in {where}")
                 + (db.t(" (sigue esperando)", " (still waiting)") if reminder else ""))
        screen = (w.get("preview") or "").strip()[-600:]
        body = f"**Tarea:** {task}\n\n```\n{screen}\n```" if screen else f"**Tarea:** {task}"
        speak = (f"{title_word}the agent in {where} is waiting for you." if en
                 else f"{title_word}el agente de {where} lo está esperando.")
    else:
        title = f"Orca · {agent} " + db.t(f"falló en {where}", f"failed in {where}")
        body = f"**Tarea:** {task}\n\nEstado: {a.get('state')}"
        speak = (f"{title_word}the agent in {where} failed." if en
                 else f"{title_word}el agente de {where} falló.")
    await notify.push("orca", title, body, {"worktree": w.get("worktreeId"), "state": a.get("state")}, speak=speak)


# ---- delegation: give Orca agents work, and answer them -----------------------

import re as _re
import shlex as _shlex
import time as _time
from pathlib import Path as _Path

TRUST_PROMPT = "trust this folder"
CONFIRM_SCREENS = ("trust this folder", "Do you want to", "Yes, I accept", "Enter to confirm")
MODES = {
    # read-only analysis: explore and propose, never edits or runs risky commands
    "plan": "--permission-mode plan",
    # makes changes: edits files freely, still asks before running shell commands
    "edit": "--permission-mode acceptEdits",
}
GUARDRAILS = (
    "\n\nReglas: trabajas en un worktree aislado en su propia rama. No hagas push, no despliegues, "
    "no toques archivos .env ni secretos. Trabaja con autonomía: edita, instala, compila y prueba sin pedir "
    "permiso. PERO detente y pregunta (y espera la respuesta) antes de: borrar archivos; cambiar el esquema "
    "de la base de datos o migraciones; tocar autenticación, seguridad o pagos; agregar o quitar dependencias; "
    "cambiar configuración de despliegue, CI o variables de entorno; un cambio que toque más de 10 archivos; "
    "o cualquier cosa irreversible. Al terminar resume en pocas líneas: qué hiciste, qué archivos, y cómo probarlo."
)


def _aliases() -> dict:
    """PROJECTS="Tu Casa Linda=~/projects/tu-casa-linda;Talos=~/Talos" -> {name: path}"""
    out = {}
    for item in filter(None, (p.strip() for p in settings.PROJECTS.split(";"))):
        name, _, path = item.partition("=")
        out[name.strip().lower()] = str(_Path(path.strip()).expanduser())
    return out


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return _re.sub(r"[^a-z0-9]+", " ", s).strip()


async def orca_projects() -> dict:
    return {"allowed_projects": _aliases(), "max_mode": settings.ORCA_DELEGATE}


async def _resolve(project: str):
    """Only allowlisted projects (PROJECTS in .env) can receive work."""
    want = _norm(project)
    for name, path in _aliases().items():
        if want and (want in _norm(name) or _norm(name) in want):
            return path
    return None


async def _auto_trust(handle: str, timeout: int = 30):
    """Accept Claude's 'trust this folder' screen for a worktree Talos just created."""
    deadline = _time.monotonic() + timeout
    while _time.monotonic() < deadline:
        await asyncio.sleep(2)
        try:
            screen = "\n".join((await run("terminal", "read", "--terminal", handle, "--screen"))
                               .get("terminal", {}).get("tail", []))
        except Exception:
            continue
        if TRUST_PROMPT in screen:
            await run("terminal", "send", "--terminal", handle, "--text", "\x1b[B")
            await asyncio.sleep(1)
            await run("terminal", "send", "--terminal", handle, "--text", "", "--enter")
            return True
        if "plan mode" in screen or "accept edits" in screen or "Percolating" in screen:
            return False  # already running
    return False


LEVELS = {"off": 0, "plan": 1, "edit": 2}

# Extra places an agent may use besides its worktree (package caches only, never config or secrets)
TOOL_CACHES = ["~/.npm", "~/.claude/plans"]  # plan mode writes its plan file there
NETWORK = ["github.com", "api.github.com", "codeload.github.com", "objects.githubusercontent.com",
           "registry.npmjs.org", "pypi.org", "files.pythonhosted.org"]
SECRETS = ["**/.env", "**/.env.*", "**/*.pem", "**/*.key", "**/id_rsa*", "**/.netrc"]


def _confinement(allowed: list) -> list:
    """Deny every path in the home folder that isn't one of `allowed` or on the way to one.

    Claude Code deny rules can't be carved out with allow rules, so instead of "deny ~ except X"
    we walk down from ~ and deny each sibling that doesn't lead to an allowed path."""
    home = _Path.home().resolve()
    allowed = [_Path(p).expanduser().resolve() for p in allowed]
    denied = []

    def walk(directory: _Path):
        for child in sorted(directory.iterdir()):
            child_r = child.resolve() if not child.is_symlink() else child
            if any(child_r == a for a in allowed):
                continue  # fully allowed subtree
            if any(a.is_relative_to(child_r) for a in allowed):
                walk(child_r)  # an ancestor of an allowed path: go one level down
            else:
                denied.append(child_r)

    walk(home)
    return denied


def agent_settings(worktree: str, repo: str, name: str) -> str:
    """Write a per-agent Claude Code settings file confining it to its worktree."""
    git_dir = str(_Path(repo) / ".git")  # worktrees write their metadata into the main repo's .git
    allowed = [worktree, git_dir] + TOOL_CACHES
    denied = _confinement(allowed)
    rules = []
    for d in denied:
        pattern = f"//{str(d).lstrip('/')}" + ("/**" if d.is_dir() else "")
        rules += [f"Read({pattern})", f"Edit({pattern})", f"Write({pattern})"]
    rules += [f"Read({p})" for p in SECRETS] + [f"Edit({p})" for p in SECRETS]
    settings_json = {
        "permissions": {"deny": rules, "defaultMode": None},
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            # routine commands run without asking: they can only write inside the worktree and reach
            # the allowlisted hosts; anything that would escape the sandbox is refused
            "autoAllowBashIfSandboxed": True,
            "filesystem": {
                "denyRead": [str(d) + ("/**" if d.is_dir() else "") for d in denied] + SECRETS,
                "allowWrite": [worktree, git_dir] + [str(_Path(c).expanduser()) for c in TOOL_CACHES],
            },
            "network": {"allowedDomains": NETWORK},
        },
    }
    settings_json["permissions"].pop("defaultMode")
    out = settings.DATA_DIR / "agent-settings" / f"{name}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(settings_json, indent=1))
    return str(out)


async def orca_delegate(project: str, task: str, mode: str = "plan") -> dict:
    allowed = settings.ORCA_DELEGATE if settings.ORCA_DELEGATE in LEVELS else "off"
    mode = mode if mode in MODES else "plan"
    if LEVELS[allowed] == 0:
        return {"error": "Delegar trabajo a agentes está desactivado (ORCA_DELEGATE=off)."}
    if LEVELS[mode] > LEVELS[allowed]:
        return {"error": f"Solo tengo permitido el modo '{allowed}'. Para que un agente modifique archivos, "
                         "el usuario debe poner ORCA_DELEGATE=edit en .env."}
    if not await is_running():
        return {"error": "Orca está cerrado. Ábrelo para poder delegar."}
    path = await _resolve(project)
    if not path:
        return {"error": f"'{project}' no está en la lista de proyectos permitidos (PROJECTS en .env).",
                "allowed": list(_aliases())}
    if not _Path(path).exists():
        return {"error": f"La ruta {path} no existe en este Mac."}
    await run("repo", "add", "--path", path)  # idempotent
    slug = "-".join(_norm(task).split()[:4]) or "tarea"
    name = f"talos-{slug}-{_time.strftime('%m%d-%H%M')}"
    wt = (await run("worktree", "create", "--repo", f"path:{path}", "--name", name)).get("worktree", {})
    prompt = task.strip() + GUARDRAILS
    # confine the agent to its worktree: no reads/writes elsewhere in ~, sandboxed shell, limited network
    confinement = agent_settings(wt["path"], path, name)
    term = (await run("terminal", "create", "--worktree", f"path:{wt['path']}", "--title", f"talos · {mode}",
                      "--command", f"cd {_shlex.quote(wt['path'])} && claude {MODES[mode]} "
                                   f"--settings {_shlex.quote(confinement)} {_shlex.quote(prompt)}")).get("terminal", {})
    asyncio.create_task(_auto_trust(term["handle"]))
    return {"ok": True, "project": project, "worktree": wt.get("displayName"), "branch": wt.get("branch"),
            "mode": mode, "terminal": term.get("handle"),
            "note": "Te aviso cuando termine o si necesita algo."}


async def orca_reply(text: str, worktree: str = "") -> dict:
    """Send text to an agent: the one in `worktree`, or the one that's waiting for you."""
    if not await is_running():
        return {"error": "Orca está cerrado."}
    terms = (await run("terminal", "list")).get("terminals", [])
    target = None
    if worktree:
        want = _norm(worktree)
        target = next((t for t in terms if want in _norm(t.get("worktreePath", "") + " " + (t.get("title") or ""))), None)
    if not target:
        waiting = [t for t in terms if any(k in (t.get("preview") or "") for k in CONFIRM_SCREENS + ("?",))]
        target = max(waiting or terms, key=lambda t: t.get("lastOutputAt") or 0, default=None)
    if not target:
        return {"error": "No encontré ningún agente activo."}
    await run("terminal", "send", "--terminal", target["handle"], "--text", text, "--enter")
    return {"ok": True, "sent_to": target.get("worktreePath"), "text": text}


TOOLS += [
    {
        "name": "orca_delegate",
        "description": "Pone a un agente de código (Claude Code en Orca) a trabajar en un proyecto, encerrado en un "
                       "worktree aislado. mode='plan' (por defecto) solo analiza y propone; mode='edit' implementa "
                       "cambios con autonomía y solo pregunta lo importante (borrar, migraciones, auth, dependencias, "
                       "despliegue). Usa 'edit' cuando el usuario pida directamente implementar/cambiar/arreglar "
                       "algo. Escribe la tarea completa y concreta.",
        "parameters": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Nombre del proyecto, p. ej. 'Tu Casa Linda'"},
                "task": {"type": "string", "description": "Qué debe hacer el agente, con todo el contexto"},
                "mode": {"type": "string", "enum": ["plan", "edit"]},
            },
            "required": ["project", "task"],
        },
        "handler": orca_delegate,
    },
    {
        "name": "orca_reply",
        "description": "Le responde a un agente de Orca que está esperando (o al del worktree indicado): "
                       "'dile que sí', 'dile que use X'.",
        "parameters": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "worktree": {"type": "string"}},
            "required": ["text"],
        },
        "handler": orca_reply,
    },
    {
        "name": "orca_projects",
        "description": "Lista los proyectos en los que se permite delegar trabajo.",
        "parameters": {"type": "object", "properties": {}},
        "handler": orca_projects,
    },
]
