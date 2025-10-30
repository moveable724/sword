from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import os

from .db import get_db, Base, engine
from .models import Trade as TradeModel, User as UserModel

app = FastAPI(title="Sword Game API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup (simple auto-migrate)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

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
def get_trades(db: Session = Depends(get_db)):
    stmt = select(TradeModel).order_by(TradeModel.created_at.desc())
    rows = db.execute(stmt).scalars().all()
    trades = [
        {
            "id": str(r.id),
            "company": r.company,
            "leverage": r.leverage,
            "type": r.trade_type,
            "quantity": r.quantity,
            "user": r.user_id,
            "createdAt": int(r.created_at.timestamp() * 1000) if r.created_at else None,
        }
        for r in rows
    ]
    return {"trades": trades}

@app.post("/api/leverage-trades", status_code=201)
def create_trade(trade: Trade, db: Session = Depends(get_db)):
    row = TradeModel(
        company=trade.company,
        leverage=trade.leverage,
        trade_type=trade.type,
        quantity=trade.quantity,
        user_id=trade.user,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "trade": {
            "id": str(row.id),
            "company": row.company,
            "leverage": row.leverage,
            "type": row.trade_type,
            "quantity": row.quantity,
            "user": row.user_id,
            "createdAt": int(row.created_at.timestamp() * 1000) if row.created_at else None,
        }
    }

@app.delete("/api/leverage-trades/{trade_id}")
def delete_trade(trade_id: str, db: Session = Depends(get_db)):
    # Accept both UUID and raw string
    row = db.get(TradeModel, trade_id)
    if not row:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(row)
    db.commit()
    return {"ok": True}

# Rankings
@app.get("/api/rankings/clubs")
def get_club_rankings(db: Session = Depends(get_db)):
    # Sum total_assets (or max_stage) per club_name
    rows = db.execute(
        select(
            UserModel.club_name,
            func.coalesce(func.sum(func.coalesce(UserModel.total_assets, UserModel.max_stage, 0)), 0),
        ).group_by(UserModel.club_name)
    ).all()
    rankings = [
        {"clubName": r[0] or "NoClub", "totalAssets": int(r[1] or 0)}
        for r in rows
    ]
    rankings.sort(key=lambda x: x["totalAssets"], reverse=True)
    return {"rankings": rankings}

@app.get("/api/rankings/users")
def get_user_rankings(db: Session = Depends(get_db)):
    rows = db.execute(select(UserModel)).scalars().all()
    rankings = [
        {
            "username": r.id,
            "totalAssets": int(r.total_assets if r.total_assets is not None else (r.max_stage or 0)),
        }
        for r in rows
    ]
    rankings.sort(key=lambda x: x["totalAssets"], reverse=True)
    return {"rankings": rankings}

# Game sync
@app.post("/api/game/sync")
def sync_game(sync_data: GameSync, db: Session = Depends(get_db)):
    row = db.get(UserModel, sync_data.userId)
    total_assets = (
        sync_data.totalAssets if sync_data.totalAssets is not None else sync_data.maxStage
    )
    if row:
        row.stage = sync_data.currentStage
        row.max_stage = sync_data.maxStage
        row.attempts = sync_data.attempts
        row.club_name = sync_data.clubName
        row.total_assets = total_assets
    else:
        row = UserModel(
            id=sync_data.userId,
            stage=sync_data.currentStage,
            max_stage=sync_data.maxStage,
            attempts=sync_data.attempts,
            club_name=sync_data.clubName,
            total_assets=total_assets,
        )
        db.add(row)
    db.commit()
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
