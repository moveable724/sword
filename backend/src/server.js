import express from 'express'
import cors from 'cors'
import { initDB } from './db.js'
import { tradesRouter } from './routes/trades.js'
import { rankingsRouter } from './routes/rankings.js'
import { gameRouter } from './routes/game.js'

const app = express()
const PORT = process.env.PORT || 8000

app.use(cors({ origin: '*'}))
app.use(express.json())

app.get('/', (_req, res) => res.json({ ok: true, service: 'sword-game-backend' }))
app.use('/api/leverage-trades', tradesRouter)
app.use('/api/rankings', rankingsRouter)
app.use('/api/game', gameRouter)

initDB().then(() => {
  app.listen(PORT, () => {
    console.log(`API listening on http://localhost:${PORT}`)
  })
})
