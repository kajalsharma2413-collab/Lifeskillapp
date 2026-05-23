<template>
  <div class="local-wrapper">
    <!-- 🔙 Back Button -->
    <button @click="goBack"
      class="absolute top-6 left-6 z-50 text-white bg-black/40 hover:bg-black/60 px-4 py-2 rounded-full backdrop-blur-md border border-white/20 shadow-md transition">
      ⬅️ Back
    </button>
    <div class="container">
      <div v-if="!assistant_Id && !loading">
        <h1 class="text-3xl font-bold"> 🎓 Choose Your AI </h1>
        <div class="container-button">
          <button @click="selectRole('story')" class="btn">📖 Story Coach</button>
          <button @click="selectRole('debate')" class="btn">🧠 Debate Coach</button>
        </div>
      </div>

      <div v-else-if="loading" class="text-center animate-fade">
        <img :src="Loading" class="w-24 h-24 mx-auto animate-spin" />
        <p class="mt-4 text-xl font-semibold text-white">Preparing your assistant...</p>
      </div>

      <div v-else>
        <div class="text-center">
          <h2 class="text-2xl font-bold mb-4">🎙️ Talking to {{ selectedRole }} Coach</h2>
          <p v-if="status" :class="[
            'status-message',
            status.includes('Connecting') ? 'connecting' : '',
            status.includes('Call started') ? 'connected' : '',
            status.includes('Ending') ? 'ending' : '',
            status.includes('❌') || status.includes('Error') ? 'error' : ''
            ]">
            {{ status }}
          </p>
          <transition name="fade">
            <div class="space-x-4">
              <!-- Start Talking Button -->
              <button v-if="!callStarted && !status.includes('Connecting')" @click="startCall" class="btn"
                :disabled="isStarting" aria-label="Start Talking">
                ▶️ Start Talking
              </button>

              <!-- End Call Button -->
              <button v-else-if="callStarted && !status.includes('Ending')" @click="endCall" class="btn"
                aria-label="End Call">
                ⏹️ End Call
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import Vapi from '@vapi-ai/web'
import { useRouter } from 'vue-router'
import Loading from '@/assets/loading.svg'

const isStarting = ref(false)
const router = useRouter()
const status = ref('')
const assistant_Id = ref(null)
const vapi_public = ref(null)
const selectedRole = ref('')
const loading = ref(false)
let vapi = null

const callStarted = ref(false)

const resetSession = async () => {
  if (vapi) {
    try {
      await vapi.stop()
      console.log('call ended by user')
    } catch (err) {
      console.warn("Failed to stop Vapi:", err)
    }
    vapi = null
  }

  assistant_Id.value = null
  selectedRole.value = ''
  status.value = ''
  loading.value = false
  callStarted.value = false
}

const selectRole = async (role) => {
  try {
    // Clean up any existing Vapi instance
    if (vapi) {
      try { await vapi.stop() } catch (e) { console.warn("Vapi cleanup failed", e) }
      vapi = null
    }

    // Always clear stale localStorage — never reuse old assistant IDs
    localStorage.removeItem(`assistant_Id_${role}`)
    localStorage.removeItem('vapi_public')

    loading.value = true
    selectedRole.value = role

    const res = await fetch('http://localhost:8000/api/v1/vapi/get-assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role })
    })

    if (!res.ok) throw new Error(`Server error: ${res.status}`)
    const data = await res.json()

    if (!data.assistant_id || !data.vapi_public) {
      throw new Error('Invalid response from server')
    }

    assistant_Id.value = data.assistant_id
    vapi_public.value = data.vapi_public

  } catch (err) {
    console.error('Failed to fetch assistant:', err)
    status.value = '❌ Failed to prepare assistant'
    assistant_Id.value = null
    selectedRole.value = ''
    vapi_public.value = null
    setTimeout(() => { status.value = '' }, 1500)
  } finally {
    loading.value = false
  }
}

const startCall = async () => {
  if (isStarting.value) return

  try {
    isStarting.value = true
    status.value = 'Connecting...'

    // Clean up any dirty/leftover Vapi instance before creating a new one
    // (fixes "KrispSDK duplicated" warning and double-call bugs)
    if (vapi) {
      try { await vapi.stop() } catch (e) {}
      vapi = null
    }

    // Request mic permission explicitly before Vapi starts
    // (fixes silent audio failure on Chrome 128+ / new browser versions)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      stream.getTracks().forEach(t => t.stop()) // release; Vapi takes over
    } catch (micErr) {
      status.value = '❌ Microphone permission denied. Please allow mic access and try again.'
      isStarting.value = false
      return
    }

    vapi = new Vapi(vapi_public.value)

    vapi.on('call-start', () => {
      console.log('Call started')
      status.value = '📞 Call started!'
      callStarted.value = true
      isStarting.value = false
    })

    vapi.on('call-end', () => {
      console.log('Call ended')
      status.value = '🛑 Call ended.'
      callStarted.value = false
      loading.value = false
      isStarting.value = false

      // Longer delay so user can read the status before reset
      setTimeout(() => {
        assistant_Id.value = null
        selectedRole.value = ''
        status.value = ''
      }, 1500)
    })

    vapi.on('error', (err) => {
      // Log full error so you can see exactly what Vapi reports in console
      console.error('Vapi error (full):', JSON.stringify(err, null, 2))
      const msg = err?.error?.message || err?.message || JSON.stringify(err)
      status.value = `❌ ${msg}`
      callStarted.value = false
      isStarting.value = false
    })

    await vapi.start(assistant_Id.value)

  } catch (err) {
    console.error('Failed to start call:', err)
    status.value = `❌ Call failed: ${err?.message || err}`
    isStarting.value = false
  }
}

const endCall = async () => {
  if (!vapi) return

  status.value = '🛑 Ending call…'
  await new Promise(r => setTimeout(r, 1500))
  await nextTick()

  await resetSession()
}

const goBack = async () => {
  await resetSession()
  router.push('/lifeskills')
}

onMounted(() => {
  // Clear ALL stale vapi assistant IDs on every mount
  ;['story', 'debate'].forEach(role => localStorage.removeItem(`assistant_Id_${role}`))
  localStorage.removeItem('vapi_public')

  window.addEventListener('beforeunload', resetSession)
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', resetSession)
})
</script>

<style scoped>
.local-wrapper {
  all: initial;
  font-family: 'Segoe UI', sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-image: url('../assets/wallhaven-73xmoo_1400x900.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.container{
  max-width: 440px;
}
h2,h1{
  color: #BD93F9;
  padding :0.5rem;
  margin: 0.5rem;
  padding-left: 48px;
  background-color: transparent;
  backdrop-filter: blur(5px);
  border-radius: 50px;
  font-size: 2.5rem;
}
.container-button {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
.btn:focus-visible {
  outline: 2px solid #93c5fd;
  outline-offset: 4px;
}
.btn {
  position: relative;
  background-color: transparent;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 9999px;
  border: 2px solid transparent;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  backdrop-filter: blur(12px);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  z-index: 0;
  overflow: hidden;
}

/* Animated glowing border effect */
.btn::before {
  content: "";
  position: absolute;
  inset: -2px;
  z-index: -1;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6, #ec4899, #3b82f6);
  background-size: 400% 400%;
  border-radius: inherit;
  animation: glowMove 6s ease infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
  filter: blur(8px);
}

/* Subtle inner glow for depth */
.btn::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background-color: rgba(255, 255, 255, 0.05);
  border-radius: inherit;
}

/* Hover state */
.btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.5),
  0 0 24px rgba(139, 92, 246, 0.4),
  inset 0 0 10px rgba(255, 255, 255, 0.08);
}

.btn:hover::before {
  opacity: 1;
}

@keyframes glowMove {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animate-fade {
  animation: fadeIn 1.5s ease-in-out infinite alternate;
}

@keyframes fadeIn {
  from { opacity: 0.3; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.status-message {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  text-align: center;
  min-width: 220px;
  border-radius: 1.5rem;
  color: white;
  background: radial-gradient(circle at top left, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.15);
  animation: bounceIn 0.8s ease, pulseSubtle 3s ease-in-out infinite;
  transition: all 0.3s ease;
}

.status-message.connected {
  background-color: rgba(34, 197, 94, 0.2);
  color: #bbf7d0;
  border-color: rgba(34, 197, 94, 0.4);
  box-shadow: 0 0 16px rgba(34, 197, 94, 0.5);
}

.status-message.connecting {
  background-color: rgba(59, 130, 246, 0.2);
  color: #dbeafe;
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 0 16px rgba(59, 130, 246, 0.4);
}

.status-message.ending {
  background-color: rgba(234, 179, 8, 0.2);
  color: #fef08a;
  border-color: rgba(234, 179, 8, 0.4);
  box-shadow: 0 0 16px rgba(234, 179, 8, 0.4);
}

.status-message.error {
  background-color: rgba(239, 68, 68, 0.2);
  color: #fecaca;
  border-color: rgba(239, 68, 68, 0.4);
  box-shadow: 0 0 16px rgba(239, 68, 68, 0.5);
}

@keyframes bounceIn {
  0% { transform: scale(0.8); opacity: 0; }
  60% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); }
}

@keyframes pulseSubtle {
  0%, 100% { transform: scale(1); opacity: 0.95; }
  50% { transform: scale(1.03); opacity: 1; }
}
</style>
