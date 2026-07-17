import { defineConfig, devices } from '@playwright/test'

const databaseUrl = process.env.DATABASE_URL
  ?? 'postgresql+asyncpg://app:app@127.0.0.1:55432/lost_found_e2e'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  globalSetup: './e2e/global-setup.ts',
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      command: '../../.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '../src/backend',
      url: 'http://127.0.0.1:8000/api/health/live',
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ...process.env,
        APP_ENV: 'e2e',
        DATABASE_URL: databaseUrl,
        AI_MODE: 'mock',
        EMBEDDING_MODE: 'mock',
      },
    },
    {
      command: 'npm run dev -- --host 127.0.0.1',
      cwd: '.',
      url: 'http://127.0.0.1:5173/login',
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        ...process.env,
        VITE_USE_MOCK: 'false',
      },
    },
  ],
})
