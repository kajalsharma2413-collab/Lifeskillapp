// src/stores/user.js
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: null,
    role: null,
    user: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
  },

  actions: {
    setUser(data) {
      this.token = data.token
      this.role = data.role
      this.user = data.user
      localStorage.setItem('user', JSON.stringify(data))
    },

    loadUser() {
      const saved = localStorage.getItem('user')
      if (saved) {
        try {
          const parsed = JSON.parse(saved)
          this.token = parsed.token || null
          this.role = parsed.role || null
          this.user = parsed.user || null
        } catch (err) {
          console.error('Error loading user from storage:', err)
        }
      }
    },

    logout() {
      this.token = null
      this.role = null
      this.user = null
      localStorage.removeItem('user')
    }
  }
})
