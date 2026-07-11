import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  token: string | null
  isAuthenticated: boolean
  user: { id: number; username: string; role: string } | null
  login: (token: string, user?: { id: number; username: string; role: string }) => void
  logout: () => void
  setUser: (user: { id: number; username: string; role: string }) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      isAuthenticated: false,
      user: null,
      login: (token, user) => set({ token, isAuthenticated: true, user: user || null }),
      logout: () => set({ token: null, isAuthenticated: false, user: null }),
      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
