<!-- App.vue -->
<template>
  <!-- if we're on /conversation, just render the page's component -->
  <div v-if="$route.name === 'conversation'">
    <router-view/>
  </div>

  <!-- otherwise, wrap every other page in your global layout -->
  <div v-else>
    <!-- Background Image Layer -->
    <div class="fixed inset-0 z-0 bg-cover bg-center" :style="{ backgroundImage: `url(${currentBackground})` }"></div>
    <!-- Cursor Glow Layer -->
    <div class="pointer-events-none fixed inset-0 z-10" :style="{ '--x': mouseX + 'px', '--y': mouseY + 'px' }"></div>

    <!-- Foreground UI -->
    <div class="relative z-20 min-h-screen bg-background/70 text-text-base font-sans" @mousemove="updateMouse">
      <Navbar />
      <main class="p-4">
        <router-view />
      </main>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import { useUserStore } from '@/stores/user'

// Images
import defaultBg from '@/assets/background.jpg'
import userBg from '@/assets/7825852.jpg'
import parentBg from '@/assets/parent.jpg'
import adminBg from '@/assets/admin.jpg'

const mouseX = ref(-999)
const mouseY = ref(-999)

function updateMouse(e) {
    mouseX.value = e.clientX
    mouseY.value = e.clientY
}

const userStore = useUserStore()
onMounted(() => userStore.loadUser())

const currentBackground = computed(() => {
    switch (userStore.role) {
        case 'user':
            return adminBg
        case 'parent':
            return parentBg
        case 'admin':
            return userBg
        default:
            return defaultBg
    }
})
</script>

<style scoped>
.pointer-events-none {
    background: radial-gradient(250px circle at var(--x) var(--y),
            rgba(139, 233, 253, 0.1),
            transparent 80%);
    transition: background 0.05s ease;
}

body {
    background: linear-gradient(180deg, #282a36 0%, #1e1f29 100%);
    font-family: 'Fredoka', sans-serif;
}
</style>
  
