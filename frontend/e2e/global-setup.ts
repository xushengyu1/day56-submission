import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

export default function globalSetup() {
  const frontendDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
  const workspaceDir = path.resolve(frontendDir, '..')
  const databaseUrl = process.env.DATABASE_URL
    ?? 'postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e'
  const result = spawnSync(
    path.join(workspaceDir, '.venv/bin/python'),
    [path.join(workspaceDir, 'src/backend/scripts/seed_e2e.py')],
    {
      cwd: path.join(workspaceDir, 'src/backend'),
      env: { ...process.env, APP_ENV: 'e2e', DATABASE_URL: databaseUrl },
      encoding: 'utf8',
    },
  )

  if (result.status !== 0) {
    const output = [result.stdout, result.stderr].filter(Boolean).join('\n').trim()
    throw new Error(`E2E seed failed (exit ${result.status ?? 'unknown'}):\n${output || 'no output'}`)
  }
}
