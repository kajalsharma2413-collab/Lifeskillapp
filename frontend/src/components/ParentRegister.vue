<template>
  <div class="flex items-center justify-center min-h-screen px-4">
    <div
      class="relative w-full max-w-2xl p-8 rounded-3xl shadow-2xl bg-white/10 backdrop-blur-xl border border-primary-light text-white transition-all duration-300 hover:shadow-glow hover:border-accent">
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
        <h2 class="text-3xl font-bold text-accent">👨‍👩‍👧 Parent Registration</h2>
        <p class="text-white/80 text-sm mt-2">
          Create your account to support your child's learning journey
        </p>
      </div>

      <!-- Registration Form -->
      <form @submit.prevent="handleSignup" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input v-model="form.first_name" type="text" placeholder="First Name" required class="input" />
        <input v-model="form.last_name" type="text" placeholder="Last Name" required class="input" />
        <input v-model="form.username" type="text" placeholder="Username" required class="input" />
        <input v-model="email" type="email" placeholder="Email" required class="input" />

        <div class="relative md:col-span-2">
          <input :type="showPassword ? 'text' : 'password'" v-model="password" placeholder="Password" required
            class="input pr-10" />
          <button type="button" @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-0 px-3 flex items-center text-white/60 hover:text-white" tabindex="-1">
            <span v-if="showPassword">🙈</span>
            <span v-else>👁️</span>
          </button>
        </div>

        <input v-model="form.age" type="number" placeholder="Age" min="18" required class="input" />

        <div class="md:col-span-2 mt-6">
          <button type="submit"
            class="w-full bg-accent hover:bg-accent-light text-black font-bold py-2 px-4 rounded-full transition duration-300">
            ✅ Register as Parent
          </button>
        </div>
      </form>

      <div class="text-center text-sm text-white/70 mt-4">
        Already have an account?
        <router-link to="/login" class="text-secondary-light font-semibold hover:underline">
          Log In
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { createUserWithEmailAndPassword } from 'firebase/auth'
import { auth } from '@/firebase'

const router = useRouter()

const showPassword = ref(false)
const email = ref('')
const password = ref('')

const form = ref({
  first_name: '',
  last_name: '',
  username: '',
  role: 'parent',
  age: null,
  grade_level: '',
  parent_code: ''
})

const backendError = ref('')
const showError = ref(false)

function showErrorMessage(message) {
  backendError.value = message
  showError.value = true
  setTimeout(() => {
    showError.value = false
  }, 5000)
}

async function handleSignup() {
  backendError.value = ''
  showError.value = false
  try {
    if (!email.value || !password.value) throw new Error('Email and password are required.')

    // Firebase sign up
    const userCredential = await createUserWithEmailAndPassword(auth, email.value, password.value)
    const firebaseUser = userCredential.user
    const token = await firebaseUser.getIdToken()

    // Save token for later API calls
    localStorage.setItem('firebase_token', token)

    // Backend registration
    const response = await fetch('/api/v1/auth/complete-registration', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firebase_id_token: token,
        first_name: form.value.first_name,
        last_name: form.value.last_name,
        username: form.value.username,
        role: form.value.role,
        age: form.value.age,
        grade_level: form.value.grade_level || "",
        parent_code: form.value.parent_code || ""
      }),
    })

    const result = await response.json().catch(() => ({}))

    if (!response.ok || !result.success) {
      throw new Error(result?.message || 'Backend registration failed.')
    }

    router.push('/login')
  } catch (err) {
    console.error('❌ Registration failed:', err)

    const code = err?.code || ''
    if (code === 'auth/email-already-in-use') {
      showErrorMessage('📧 This email is already registered.')
    } else if (code === 'auth/weak-password') {
      showErrorMessage('🔑 Password should be at least 6 characters long.')
    } else {
      showErrorMessage(err.message || '❌ Registration failed. Please try again.')
    }
  }
}
</script>

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
