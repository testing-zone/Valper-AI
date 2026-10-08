# TALOS — asistente personal

> Talos era el gigante de bronce que custodiaba Creta dando tres vueltas a la isla cada día. Este vigila tus noticias, tu agenda y tus pendientes.

Asistente personal que corre en tu computador. Lo usas por voz o por texto, te avisa solo de lo importante, recuerda lo que le enseñas y le delega a Claude Code las investigaciones largas.

## Qué hace

| Función | Cómo |
|---|---|
| **Conversar por voz o texto** | Whisper large-v3-turbo en la GPU del Mac con mlx, unos 0,6 s (oído) → Qwen3.6-35B en TotalGPT con herramientas (cerebro) → Kokoro alojado en Infermatic, con más de 40 voces y mezclas (voz). `Ctrl+Espacio` activa el micrófono |
| **Español / inglés** | Selector ES · EN · AUTO, con una voz por idioma: *Mayordomo* en español y *Butler* británico en inglés. Los boletines también salen en el idioma elegido |
| **Filtros de voz** | Natural, Colossus (modulación en anillo y tono metálico), Radio y Mansión (reverberación). Se aplican en el navegador |
| **Boletín cada 3 horas** | Clima (ahora, hoy y mañana) de tus ciudades, dólar, noticias locales, lanzamientos de modelos de IA, secciones extra (p. ej. inmobiliario) y titulares. **Lee los artículos completos** y resume lo que dicen, no solo el titular. Solo incluye lo nuevo desde el boletín anterior, y lo dice en voz alta |
| **Preguntas de seguimiento** | Los artículos leídos quedan guardados unos días: "¿qué pasó exactamente con X?" se responde con el texto real |
| **Noticias locales** | Todos los días a las 12:00 |
| **Pendientes de Jira** | De lunes a viernes a las 8:00, en tono de "oye, te está faltando esto" |
| **Recordatorios** | "Recuérdame mañana a las 9 llamar al banco". Pueden ser únicos, diarios, de lunes a viernes o semanales |
| **Memoria** | "Guarda cómo se despliega X". Se guarda como notas markdown enlazadas con `[[Título]]` en `data/memory/`, y la carpeta se puede abrir en Obsidian |
| **Investigación profunda** | "Investiga a fondo X". Talos lanza `claude -p` en segundo plano. Usa tu suscripción de claude.ai, no la API y el reporte aparece en la pestaña Investigación |
| **Avisos** | Tarjetas en el feed de la interfaz, notificación de macOS y voz para los recordatorios |

## Instalar y usar

```bash
./scripts/talos.sh setup      # dependencias, entorno Python 3.11 y build de la interfaz
# edita .env: TOTALGPT_API_KEY, tus ciudades (LOCATIONS), moneda, horarios...
cp persona.example.md data/persona.md   # opcional: la personalidad de tu asistente
./scripts/talos.sh start      # abre http://localhost:8000
./scripts/talos.sh install    # o déjalo corriendo siempre en segundo plano (arranca con el Mac)
```

La primera vez que arranca descarga el modelo de Whisper, así que tarda unos minutos. La voz se genera en Infermatic; si prefieres generarla en tu Mac, pon `TTS_PROVIDER=local`.

Para desarrollar: `./scripts/talos.sh dev` levanta el backend con recarga automática y React en el puerto 3000.

## Lo personal no va a git

El código es genérico. Todo lo tuyo vive en archivos que git ignora:

| Archivo | Qué guarda |
|---|---|
| `.env` | claves, ciudades y coordenadas, moneda, horarios, cómo te llama (`USER_TITLE`) |
| `data/persona.md` | personalidad y tono del asistente |
| `data/talos.db` | conversaciones, boletines, recordatorios, artículos leídos, preferencias de voz e idioma |
| `data/memory/*.md` | tus notas y tu perfil |

Plantillas: [.env.example](.env.example) y [persona.example.md](persona.example.md).

## Arquitectura

```
backend/app/
  main.py            FastAPI: API, programador de tareas y la interfaz ya compilada en un solo puerto
  agent.py           ciclo del agente: prompt + memoria + historial → LLM → herramientas → respuesta
  briefings.py       resúmenes programados (resumen, noticias locales, Jira)
  scheduler.py       horarios (APScheduler, hora de Bogotá)
  core/              config (.env), SQLite, eventos en vivo (SSE)
  services/          llm (TotalGPT), stt (Whisper), tts (Kokoro: Infermatic o local)
  tools/             clima, noticias, memoria, recordatorios, investigación, jira, notificaciones
frontend/src/        React, consola retrofuturista: Diálogo, Boletines, Investigación, Memoria, Agenda
data/                (no va a git) talos.db, memory/*.md, research/<id>/, logs/
```

**Agregar una integración** (servidores de GPU, ComfyUI, Orca): crea `backend/app/tools/<nombre>.py` con una lista `TOOLS` (`name`, `description`, `parameters` en JSON Schema y un `handler` asíncrono) y regístrala en `tools/__init__.py`. El LLM la empieza a usar sin más cambios.

**Tool calling**: con Qwen3.6 se usan las llamadas nativas de OpenAI y el "thinking" va apagado (`LLM_THINKING=false`), así responde en 1–4 s. Si cambias a un modelo sin tool-calling nativo, Talos cambia solo a etiquetas `<tool_call>` en el prompt (estilo Hermes), que funcionan con casi cualquier modelo Qwen, Llama o Mistral.

## API

| | |
|---|---|
| `POST /api/chat` | `{"message": "..."}` → respuesta y herramientas usadas |
| `POST /api/conversation` | audio (multipart `audio_file`) → transcripción y respuesta |
| `POST /api/tts` | `{"text", "voice"}` → audio |
| `GET /api/voices` | catálogo de voces |
| `GET /api/feed` · `POST /api/briefings/{digest\|local\|jira}/run` | feed y disparo manual de resúmenes |
| `GET/POST/DELETE /api/reminders` | recordatorios |
| `GET /api/notes` · `GET /api/notes/{slug}` · `PUT /api/notes` | memoria |
| `GET/POST /api/research` · `GET /api/research/{id}` | investigaciones con Claude Code |
| `GET /api/events` | eventos en vivo (SSE) |
| `GET /api/llm/models` | modelos disponibles en TotalGPT |

Documentación interactiva en http://localhost:8000/docs

## Notas

- **Límite de TotalGPT:** 18 peticiones por minuto. Talos reintenta solo si lo alcanza.
- **Decisión de herramientas:** en el primer paso Qwen razona brevemente (thinking) para decidir si usar una herramienta. Sin eso respondía con datos viejos del historial. Las preguntas de clima, noticias, Jira o recordatorios fuerzan la herramienta directamente.
- **Diagrama del estado:** la lámina 188 de la *Anatomía de Gray* (1918, dominio público), vectorizada con potrace.

## Ideas tomadas de otros proyectos

- **OpenClaw / Clawdbot**: memoria en markdown editable por humanos, un perfil del usuario siempre en el contexto, resúmenes con horario y avisos proactivos.
- **isair/jarvis**: palabra de activación, herramientas al estilo MCP y grafo de conocimiento (aquí, enlaces `[[...]]` y backlinks).
- **Hermes / Qwen**: el formato `<tool_call>` para modelos sin tool-calling nativo.

## Siguiente

- [ ] Palabra de activación "Talos" con openWakeWord y tecla global, desde un pequeño programa de escritorio
- [ ] Avisos por Telegram al celular
- [ ] Herramientas para los servidores de modelos de video, ComfyUI y Orca
- [ ] Búsqueda semántica en la memoria con `Qwen3-Embedding-8B`, que ya está disponible en TotalGPT
