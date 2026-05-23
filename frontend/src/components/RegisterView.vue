<template>
  <div class="flex items-center justify-center min-h-screen px-4">
    <div
      class="relative w-full max-w-2xl p-8 rounded-3xl shadow-2xl bg-white/10 backdrop-blur-lg border border-primary-light text-white transition-all duration-300 hover:shadow-glow hover:border-accent">
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
        <h2 class="text-3xl font-extrabold text-accent animate-bounce-once">
          🎉 Create Adventure Account
        </h2>
        <p class="text-white/70 text-sm mt-2">Let’s begin your Life Skills journey!</p>
      </div>

      <!-- Registration Form -->
      <form @submit.prevent="handleSignup" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <input v-model="form.first_name" type="text" placeholder="First Name" required class="input" />
        <input v-model="form.last_name" type="text" placeholder="Last Name" required class="input" />
        <input v-model="form.username" type="text" placeholder="Username" required class="input" />
        <input v-model="form.email" type="email" placeholder="Email" required class="input" />

        <!-- Password Field with Toggle -->
        <div class="relative md:col-span-2">
          <input :type="showPassword ? 'text' : 'password'" v-model="form.password" placeholder="Password" required
            class="input pr-10" />
          <button type="button" @click="showPassword = !showPassword"
            class="absolute inset-y-0 right-0 px-3 flex items-center text-white/60 hover:text-white" tabindex="-1">
            <span v-if="showPassword">🙈</span>
            <span v-else>👁️</span>
          </button>
        </div>

        <input v-model="form.age" type="number" placeholder="Age (8-14)" min="8" max="14" required class="input" />

        <!-- Grade Level Dropdown -->
        <select v-model="form.grade_level" required class="input bg-neutral-dark text-white">
          <option value="" class="text-black">Select Grade</option>
          <option value="I" class="text-black">I</option>
          <option value="II" class="text-black">II</option>
          <option value="III" class="text-black">III</option>
          <option value="IV" class="text-black">IV</option>
          <option value="V" class="text-black">V</option>
          <option value="VI" class="text-black">VI</option>
          <option value="VII" class="text-black">VII</option>
          <option value="VIII" class="text-black">VIII</option>
        </select>

        <input v-model="form.parent_code" type="text" placeholder="Parent Code" required class="input" />

        <!-- Help -->
        <div class="md:col-span-2 flex items-center gap-4 mt-2 text-white/70 text-sm">
          Get Parent Code
          <router-link to="/register-parent" class="text-secondary-light font-semibold hover:underline">
            here
          </router-link>
        </div>

        <!-- Submit -->
        <div class="md:col-span-2 mt-6">
          <button type="submit"
            class="w-full bg-accent hover:bg-accent-light text-black font-bold py-2 px-4 rounded-full transition duration-300">
            🚀 Let’s Begin!
          </button>
        </div>
      </form>

      <!-- Already have account -->
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
import { createUserWithEmailAndPassword } from 'firebase/auth'
import { auth } from '@/firebase'
import { useRouter } from 'vue-router'

const router = useRouter()

const form = ref({
  email: '',
  password: '',
  username: '',
  first_name: '',
  last_name: '',
  role: 'user',
  age: null,
  grade_level: '',
  parent_code: '',
})

const showPassword = ref(false)
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

  if (form.value.age < 8 || form.value.age > 14) {
    showErrorMessage('⚠️ Age must be between 8 and 14.')
    return
  }

  try {
    // Firebase registration
    const userCredential = await createUserWithEmailAndPassword(auth, form.value.email, form.value.password)
    const firebaseUser = userCredential.user
    const idToken = await firebaseUser.getIdToken()

    // Store token
    localStorage.setItem('firebase_token', idToken)

    // Backend registration
    const response = await fetch('/api/v1/auth/complete-registration', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        firebase_id_token: idToken,
        username: form.value.username,
        first_name: form.value.first_name,
        last_name: form.value.last_name,
        role: form.value.role,
        age: form.value.age,
        grade_level: form.value.grade_level || '',
        parent_code: form.value.parent_code || '',
      }),
    })

    const result = await response.json().catch(() => ({}))

    if (!response.ok || !result.success) {
      throw new Error(result?.message || 'Backend registration failed.')
    }

    router.push('/login')
  } catch (err) {
    console.error('❌ Registration Error:', err)
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

select {
  appearance: none;
  background-image: url('data:image/svg+xml;charset=UTF-8,<svg fill="white" viewBox="0 0 20 20"><path d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 10.88l3.71-3.65a.75.75 0 0 1 1.06 1.06l-4.24 4.17a.75.75 0 0 1-1.06 0L5.21 8.29a.75.75 0 0 1 .02-1.08z"/></svg>');
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1.25rem 1.25rem;
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
