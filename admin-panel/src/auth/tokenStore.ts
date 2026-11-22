export type AuthTokens = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  refresh_expires_in: number
  stored_at?: number
}

const STORAGE_KEY = 'admin.auth.tokens'

export function getTokens(): AuthTokens | null {
  const saved = sessionStorage.getItem(STORAGE_KEY)
  if (!saved) return null

  try {
    return JSON.parse(saved) as AuthTokens
  } catch {
    sessionStorage.removeItem(STORAGE_KEY)
    return null
  }
}

export function saveTokens(tokens: AuthTokens): AuthTokens {
  const storedTokens = { ...tokens, stored_at: Date.now() }
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify(storedTokens))
  return storedTokens
}

export function clearTokens() {
  sessionStorage.removeItem(STORAGE_KEY)
}
