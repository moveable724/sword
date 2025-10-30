import { Router } from 'express'
import { db } from '../db.js'

export const gameRouter = Router()

// Sync current user game info
// body: { userId, currentStage, maxStage, attempts }
gameRouter.post('/sync', async (req, res) => {
  const { userId, currentStage = 0, maxStage = 0, attempts = 0, clubName, totalAssets } = req.body || {}
  if (!userId) return res.status(400).json({ error: 'userId is required' })

  await db.read()
  db.data.users ||= []
  const users = db.data.users
  const idx = users.findIndex(u => u.id === userId)
  const payload = {
    id: userId,
    stage: Number(currentStage) || 0,
    maxStage: Number(maxStage) || 0,
    attempts: Number(attempts) || 0,
    clubName: clubName || users[idx]?.clubName || null,
    totalAssets: totalAssets ?? users[idx]?.totalAssets ?? (Number(maxStage) || 0)
  }
  if (idx >= 0) users[idx] = { ...users[idx], ...payload }
  else users.push(payload)
  await db.write()
  res.json({ ok: true })
})
