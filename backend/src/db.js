import { Low } from 'lowdb'
import { JSONFile } from 'lowdb/node'
import path from 'node:path'
import fs from 'node:fs'

const dataDir = path.resolve(process.cwd(), 'data')
const dbFile = path.join(dataDir, 'db.json')

if (!fs.existsSync(dataDir)) {
  fs.mkdirSync(dataDir, { recursive: true })
}

const defaultData = {
  trades: [],
  users: [],
  clubs: []
}

const adapter = new JSONFile(dbFile)
export const db = new Low(adapter, defaultData)

export async function initDB() {
  await db.read()
  db.data ||= JSON.parse(JSON.stringify(defaultData))
  await db.write()
}
