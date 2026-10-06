/**
 * Application Configuration
 * 
 * Centralized place for all environment-based variables.
 * Update your .env.local / .env.production files to change these values.
 */

export const config = {
  // ============================================================
  // API
  // ============================================================
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "https://mines-signal-eight.vercel.app",

  // ============================================================
  // APP INFO
  // ============================================================
  appName: process.env.NEXT_PUBLIC_APP_NAME || "Mines Signal System",
  appEnv: process.env.NEXT_PUBLIC_APP_ENV || "development",

  // ============================================================
  // FEATURE FLAGS (optional, handy for toggling features)
  // ============================================================
  isDevelopment: process.env.NEXT_PUBLIC_APP_ENV !== "production",
  isProduction: process.env.NEXT_PUBLIC_APP_ENV === "production",

  // ============================================================
  // API ENDPOINTS (optional - helps avoid typos across the app)
  // ============================================================
  endpoints: {
    auth: "/api/auth",
    signals: "/api/signals",
    results: "/api/results",
    models: "/api/models",
    engines: "/api/engines",
    performance: "/api/performance",
    dashboard: "/api/dashboard",
    telegram: "/api/telegram",
    health: "/api/health",
  },
} as const;

export default config;