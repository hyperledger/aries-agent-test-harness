import { postJson, get } from './httpUtils'
import os from 'os'
import path from 'path'
import { promises as fs } from 'fs'

export async function registerPublicDid(ledgerUrl: string, seed: string, alias?: string) {
  const data = {
    alias,
    seed,
    role: 'TRUST_ANCHOR',
  }

  await postJson(`${ledgerUrl}/register`, data)
}

export function getRandomSeed() {
  const min = 100000
  const max = 999999

  const randomNum = Math.floor(Math.random() * (max - min) + min)

  return `my_seed_000000000000000000${randomNum}`
}

export async function getGenesisPath(
  genesisFile?: string,
  genesisUrl?: string,
  ledgerUrl?: string,
  dockerHost?: string
) {
  // If the genesis file is present, we already have the path
  if (genesisFile) return genesisFile

  let genesisTransactionUrl: string

  if (genesisUrl) genesisTransactionUrl = genesisUrl
  else if (ledgerUrl) genesisTransactionUrl = `${ledgerUrl}/genesis`
  else genesisTransactionUrl = `http://${dockerHost}:9000/genesis`

  const result = await get(genesisTransactionUrl)
  const genesis = await result.text()
  const genesisPath = path.join(os.tmpdir(), 'genesis.txn')
  await fs.writeFile(genesisPath, genesis)

  return genesisPath
}
