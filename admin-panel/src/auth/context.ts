import { createContext } from 'react'

export type AuthContextValue = {
  isAuthenticated: boolean
  accessToken: string | null
  login: (email: string, senha: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)
