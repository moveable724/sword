from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from pathlib import Path
from datetime import datetime
import uuid

app = FastAPI(title="Sword Game API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 데이터 디렉토리 설정
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_FILE = DATA_DIR / "db.json"

# 초기 DB 구조
DEFAULT_DATA = {
    "trades": [],
    "users": [],
    "clubs": []
}

# DB 초기화
def init_db():
    if not DB_FILE.exists():
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)

def read_db():
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

init_db()

# ===== Models =====
class Trade(BaseModel):
    company: str
    leverage: int
    type: str  # 'leverage' | 'inverse'
    quantity: int
    user: str

class TradeResponse(BaseModel):
    id: str
    company: str
    leverage: int
    type: str
    quantity: int
    user: str
    createdAt: int

class GameSync(BaseModel):
    userId: str
    currentStage: int = 0
    maxStage: int = 0
    attempts: int = 0
    clubName: Optional[str] = None
    totalAssets: Optional[int] = None

# ===== Routes =====

@app.get("/")
def health_check():
    return {"ok": True, "service": "sword-game-backend"}

# Trades
@app.get("/api/leverage-trades")
def get_trades():
    db = read_db()
    return {"trades": db.get("trades", [])}

@app.post("/api/leverage-trades", status_code=201)
def create_trade(trade: Trade):
    db = read_db()
    new_trade = {
        "id": str(uuid.uuid4()),
        "company": trade.company,
        "leverage": trade.leverage,
        "type": trade.type,
        "quantity": trade.quantity,
        "user": trade.user,
        "createdAt": int(datetime.now().timestamp() * 1000)
    }
    db["trades"].append(new_trade)
    write_db(db)
    return {"trade": new_trade}

@app.delete("/api/leverage-trades/{trade_id}")
def delete_trade(trade_id: str):
    db = read_db()
    before = len(db["trades"])
    db["trades"] = [t for t in db["trades"] if t["id"] != trade_id]
    after = len(db["trades"])
    
    if before == after:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    write_db(db)
    return {"ok": True}

# Rankings
@app.get("/api/rankings/clubs")
def get_club_rankings():
    db = read_db()
    users = db.get("users", [])
    
    club_totals = {}
    for user in users:
        club = user.get("clubName", "NoClub")
        assets = user.get("totalAssets", user.get("maxStage", 0))
        club_totals[club] = club_totals.get(club, 0) + assets
    
    rankings = [
        {"clubName": club, "totalAssets": total}
        for club, total in club_totals.items()
    ]
    rankings.sort(key=lambda x: x["totalAssets"], reverse=True)
    
    return {"rankings": rankings}

@app.get("/api/rankings/users")
def get_user_rankings():
    db = read_db()
    users = db.get("users", [])
    
    rankings = [
        {
            "username": user.get("id"),
            "totalAssets": user.get("totalAssets", user.get("maxStage", 0))
        }
        for user in users
    ]
    rankings.sort(key=lambda x: x["totalAssets"], reverse=True)
    
    return {"rankings": rankings}

# Game sync
@app.post("/api/game/sync")
def sync_game(sync_data: GameSync):
    db = read_db()
    users = db.get("users", [])
    
    user_idx = next((i for i, u in enumerate(users) if u.get("id") == sync_data.userId), None)
    
    user_data = {
        "id": sync_data.userId,
        "stage": sync_data.currentStage,
        "maxStage": sync_data.maxStage,
        "attempts": sync_data.attempts,
        "clubName": sync_data.clubName,
        "totalAssets": sync_data.totalAssets if sync_data.totalAssets is not None else sync_data.maxStage
    }
    
    if user_idx is not None:
        users[user_idx] = {**users[user_idx], **user_data}
    else:
        users.append(user_data)
    
    db["users"] = users
    write_db(db)
    
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
