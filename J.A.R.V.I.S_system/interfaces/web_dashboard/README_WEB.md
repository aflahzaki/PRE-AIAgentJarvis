# J.A.R.V.I.S Web Dashboard

A beautiful, dark-themed web interface for interacting with the J.A.R.V.I.S AI assistant system. Built with FastAPI (backend) and vanilla JavaScript (frontend).

## Features

- **AI Chat** - ChatGPT-style conversation interface with the J.A.R.V.I.S orchestrator
- **Task Management** - Full CRUD for tasks with priority, status, and category filters
- **Knowledge Base** - Store, browse, and search personal knowledge entries
- **Journal** - Daily reflections with mood tracking, highlights, and challenges
- **Habit Tracking** - Define habits and track daily completions with visual indicators
- **System Status** - Real-time view of orchestrator, providers, and database health

## Prerequisites

- Python 3.10+
- FastAPI and uvicorn installed
- J.A.R.V.I.S core system configured (database, API keys)

## Installation

1. Install dependencies (from `J.A.R.V.I.S_system/` directory):

```bash
pip install -r requirements_v2.txt
```

2. Configure environment variables in `.env`:

```bash
# Web Dashboard settings
WEB_HOST=0.0.0.0
WEB_PORT=8000
```

3. Ensure database is configured (see main project `.env.example`).

## Running

From the `J.A.R.V.I.S_system/` directory:

```bash
python run_web.py
```

The dashboard will be available at `http://localhost:8000`.

## Architecture

```
interfaces/web_dashboard/
    __init__.py          - Package init with graceful import
    app.py               - FastAPI app setup (CORS, static files, routes)
    routes/
        __init__.py      - Routes package
        chat.py          - POST /api/chat
        tasks.py         - CRUD /api/tasks
        knowledge.py     - /api/knowledge + search
        journals.py      - /api/journals
        habits.py        - /api/habits + logging
        status.py        - GET /api/status
    static/
        index.html       - Single-page application
        style.css        - JARVIS dark theme (cyan/teal accent)
        app.js           - Vanilla JS frontend logic
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI |
| GET | `/api/tasks` | List tasks (query: status, category) |
| POST | `/api/tasks` | Create a task |
| PUT | `/api/tasks/{id}` | Update a task |
| DELETE | `/api/tasks/{id}` | Delete a task |
| GET | `/api/knowledge` | List all knowledge |
| POST | `/api/knowledge` | Add knowledge entry |
| GET | `/api/knowledge/search?q=...` | Search knowledge |
| GET | `/api/journals` | List journal entries |
| POST | `/api/journals` | Create journal entry |
| GET | `/api/habits` | List active habits |
| POST | `/api/habits` | Create a habit |
| POST | `/api/habits/{id}/log` | Log habit completion |
| GET | `/api/status` | System health status |

## Design

The frontend uses a JARVIS-inspired dark theme with:
- Primary backgrounds: `#0d1117`, `#1a1a2e`, `#16213e`
- Accent color: `#00bcd4` (cyan/teal)
- Holographic glow effects and smooth transitions
- Responsive layout that works on desktop and mobile
- No external JavaScript frameworks required

## Troubleshooting

- **FastAPI not found**: Run `pip install fastapi uvicorn`
- **Database errors**: Check `.env` database configuration
- **Orchestrator unavailable**: Ensure API keys are set for at least one provider
- **Static files not loading**: The dashboard serves files from the `static/` directory relative to `app.py`
