import { Router } from 'express'
import { db } from '../db.js'
import { nanoid } from 'nanoid'

export const tradesRouter = Router()

// GET all leverage trades
tradesRouter.get('/', async (_req, res) => {
  await db.read()
  return res.json({ trades: db.data.trades || [] })
})

// POST new leverage trade
tradesRouter.post('/', async (req, res) => {
  const { company, leverage, type, quantity, user } = req.body || {}
  if (!company || !leverage || !type || !quantity || !user) {
    return res.status(400).json({ error: 'Missing required fields' })
  }
  const trade = {
    id: nanoid(),
    company,
    leverage: Number(leverage),
    type, // 'leverage' | 'inverse'
    quantity: Number(quantity),
    user,
    createdAt: Date.now()
  }
  await db.read()
  db.data.trades ||= []
  db.data.trades.push(trade)
  await db.write()
  return res.status(201).json({ trade })
})

// DELETE trade by id
tradesRouter.delete('/:id', async (req, res) => {
  const { id } = req.params
  await db.read()
  const before = db.data.trades?.length || 0
  db.data.trades = (db.data.trades || []).filter(t => t.id !== id)
  await db.write()
  const after = db.data.trades.length
  if (after === before) return res.status(404).json({ error: 'Not found' })
  return res.json({ ok: true })
})
