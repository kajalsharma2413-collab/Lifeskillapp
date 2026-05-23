<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { signInWithEmailAndPassword } from 'firebase/auth'
import { auth } from '@/firebase'

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const idTokenDisplay = ref('')
const backendError = ref('')
const showError = ref(false)

const demoAccounts = [
  { role: 'Parent', emoji: '👨‍👩‍👧', email: 'kkss12@gmail.com', password: 'kkss12' },
  { role: 'Children', emoji: '🧒', email: 'ssrr12@gmail.com', password: 'ssrr12' },
  { role: 'Admin', emoji: '🛡️', email: 'admin12@gmail.com', password: 'admin12' },
]

const copiedField = ref(null)

function fillDemo(account) {
  email.value = account.email
  password.value = account.password
}

async function copyToClipboard(text, key) {
  try {
    await navigator.clipboard.writeText(text)
    copiedField.value = key
    setTimeout(() => { copiedField.value = null }, 2000)
  } catch {
    // fallback for older browsers
    const el = document.createElement('textarea')
    el.value = text
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    copiedField.value = key
    setTimeout(() => { copiedField.value = null }, 2000)
  }
}

const userStore = useUserStore()
const router = useRouter()

function showErrorMessage(message) {
  backendError.value = message
  showError.value = true

  setTimeout(() => {
    showError.value = false
  }, 5000)
}

async function handleLogin() {
  backendError.value = ''
  showError.value = false
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email.value, password.value)
    const firebaseUser = userCredential.user
    const idToken = await firebaseUser.getIdToken()

    // Save token & firebase user
    idTokenDisplay.value = idToken
    localStorage.setItem('firebase_token', idToken)
    localStorage.setItem('firebase_user', JSON.stringify(firebaseUser)) // <-- ADDED

    console.log(idToken)

    const response = await fetch('/api/v1/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ firebase_id_token: idToken }),
    })

    const result = await response.json()

    if (!response.ok || !result.success) {
      throw new Error(result?.message || 'Authentication failed')
    }

    const userData = result?.data?.user
    if (!userData?.role) throw new Error('No user role found in backend response')

    userStore.setUser({ token: idToken, role: userData.role, user: userData })

    switch (userData.role) {
      case 'parent': router.push('/parent-dashboard'); break
      case 'user': router.push('/student-dashboard'); break
      case 'admin': router.push('/admin-dashboard'); break
      default: showErrorMessage('Unknown user role returned from backend')
    }
  } catch (err) {
    console.error('❌ Login failed:', err)

    const code = err?.code || ''
    if (code === 'auth/wrong-password') {
      showErrorMessage('⚠️ Incorrect password. Please try again.')
    } else if (code === 'auth/user-not-found') {
      showErrorMessage('📧 Email not found. Please sign up first.')
    } else if (code === 'auth/invalid-credential') {
      showErrorMessage('🔑 Invalid email or password. Please try again.')
    } else {
      showErrorMessage('❌ ' + (err.message || 'Login failed. Please try again.'))
    }
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen px-4">
    <div
      class="relative w-full max-w-md p-8 rounded-3xl shadow-2xl bg-white/10 backdrop-blur-xl border border-primary-light text-white transition-all duration-300">
      <!-- Error Box -->
      <transition name="fade">
        <div v-if="showError"
          class="bg-red-500/20 border border-red-500 text-red-300 px-4 py-3 rounded-lg mb-4 flex justify-between items-start space-x-2">
          <span>{{ backendError }}</span>
          <button @click="showError = false" class="text-red-400 hover:text-red-200">✖</button>
        </div>
      </transition>

      <!-- Header -->
      <div class="text-center mb-6">
        <h2 class="text-3xl font-extrabold text-accent">👋 Welcome Back, Pupil!</h2>
        <p class="text-white/70 text-sm mt-2">Log in to continue your Life Skills adventure</p>
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-semibold text-white mb-1">Email</label>
          <input id="email" v-model="email" type="email" required placeholder="Enter your email" class="input" />
        </div>
        <div class="relative">
          <label for="password" class="block text-sm font-semibold text-white mb-1">Password</label>
          <input id="password" :type="showPassword ? 'text' : 'password'" v-model="password" required
            placeholder="Enter your password" class="input pr-10" />
          <button type="button" @click="showPassword = !showPassword"
            class="absolute top-8 right-3 text-white/60 hover:text-white z-10" tabindex="-1">
            <span v-if="showPassword">🙈</span>
            <span v-else>👁️</span>
          </button>
        </div>
        <button type="submit"
          class="w-full bg-accent hover:bg-accent-light text-black font-bold py-2 px-4 rounded-full transition duration-300">
          🚀 Let’s Go!
        </button>
      </form>

      <!-- Demo Accounts -->
      <div class="mt-6">
        <p class="text-center text-xs font-semibold text-white/50 uppercase tracking-widest mb-3">Demo Accounts</p>
        <div class="space-y-2">
          <div
            v-for="account in demoAccounts"
            :key="account.role"
            class="rounded-xl border border-white/20 bg-white/5 px-3 py-2 hover:bg-white/10 transition duration-200"
          >
            <div class="flex items-center justify-between mb-1">
              <span class="text-xs font-bold text-accent tracking-wide">{{ account.emoji }} {{ account.role }}</span>
              <button
                type="button"
                @click="fillDemo(account)"
                class="text-[10px] bg-accent/20 hover:bg-accent/40 text-accent font-semibold px-2 py-0.5 rounded-full transition"
              >
                Use this
              </button>
            </div>
            <div class="flex items-center justify-between text-xs text-white/70">
              <span class="truncate mr-1">{{ account.email }}</span>
              <button
                type="button"
                @click="copyToClipboard(account.email, account.role + '-email')"
                class="shrink-0 text-white/40 hover:text-accent transition text-[11px]"
                :title="'Copy email'"
              >
                {{ copiedField === account.role + '-email' ? '✅' : '📋' }}
              </button>
            </div>
            <div class="flex items-center justify-between text-xs text-white/70 mt-0.5">
              <span class="font-mono tracking-wider mr-1">{{ account.password }}</span>
              <button
                type="button"
                @click="copyToClipboard(account.password, account.role + '-pass')"
                class="shrink-0 text-white/40 hover:text-accent transition text-[11px]"
                :title="'Copy password'"
              >
                {{ copiedField === account.role + '-pass' ? '✅' : '📋' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Signup Prompt -->
      <div class="mt-6 text-center text-sm text-white/70">
        New here?
        <router-link to="/join-us" class="text-secondary-light font-semibold hover:underline">
          Create an account
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input {
  @apply w-full px-4 py-2 bg-white/20 border border-white/30 text-white placeholder-white/60 rounded-lg focus:ring-2 focus:ring-accent focus:outline-none text-sm backdrop-blur;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
