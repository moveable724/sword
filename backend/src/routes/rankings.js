import { Router } from 'express'
import { db } from '../db.js'

export const rankingsRouter = Router()

// Clubs ranking
rankingsRouter.get('/clubs', async (_req, res) => {
  await db.read()
  // Aggregate by clubName; if missing, group under 'NoClub'
  const users = db.data.users || []
  const byClub = new Map()
  for (const u of users) {
    const club = u.clubName || 'NoClub'
    const score = Number(u.totalAssets ?? u.maxStage ?? 0)
    byClub.set(club, (byClub.get(club) || 0) + score)
  }
  const rankings = Array.from(byClub.entries())
    .map(([clubName, totalAssets]) => ({ clubName, totalAssets }))
    .sort((a, b) => b.totalAssets - a.totalAssets)
  res.json({ rankings })
})

// Users ranking
rankingsRouter.get('/users', async (_req, res) => {
  await db.read()
  const users = (db.data.users || []).map(u => ({
    username: u.id,
    totalAssets: Number(u.totalAssets ?? u.maxStage ?? 0)
  }))
  users.sort((a, b) => b.totalAssets - a.totalAssets)
  res.json({ rankings: users })
})
