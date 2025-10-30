# Sword Game Backend

Express.js REST API for the Sword Enhancement Game.

## Features

- **Trade Management**: POST/GET/DELETE leverage trades
- **Rankings**: Club and user rankings
- **Game Sync**: Save/sync game progress

## Tech Stack

- Node.js + Express
- LowDB (JSON file database)
- CORS enabled

## API Endpoints

- `GET /` - Health check
- `GET /api/leverage-trades` - Get all trades
- `POST /api/leverage-trades` - Create trade
- `DELETE /api/leverage-trades/:id` - Delete trade
- `GET /api/rankings/clubs` - Club rankings
- `GET /api/rankings/users` - User rankings
- `POST /api/game/sync` - Sync game progress

## Local Development

```bash
cd backend
npm install
npm run dev  # Auto-reload on changes
```

## Production

```bash
npm start
```

Server runs on port 8000 by default (configurable via `PORT` env var).
