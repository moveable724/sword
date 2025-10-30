# Sword Game Backend

FastAPI REST API for the Sword Enhancement Game.

## Features

- **Trade Management**: POST/GET/DELETE leverage trades
- **Rankings**: Club and user rankings
- **Game Sync**: Save/sync game progress

## Tech Stack

- Python 3.11+
- FastAPI
- Uvicorn (ASGI server)
- JSON file database

## API Endpoints

- `GET /` - Health check
- `GET /api/leverage-trades` - Get all trades
- `POST /api/leverage-trades` - Create trade
- `DELETE /api/leverage-trades/{id}` - Delete trade
- `GET /api/rankings/clubs` - Club rankings
- `GET /api/rankings/users` - User rankings
- `POST /api/game/sync` - Sync game progress

## Local Development

```bash
cd backend
pip install -r requirements.txt
# set DATABASE_URL for Postgres (Neon/Supabase/Railway) OR run with local SQLite fallback
# Example (Neon):
# set DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
python main.py
# or
uvicorn main:app --reload --port 8000
```

## Production

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Server runs on port 8000 by default (configurable via `PORT` env var).
