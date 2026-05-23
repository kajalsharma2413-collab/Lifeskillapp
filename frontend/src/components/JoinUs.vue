<template>
  <div class="min-h-screen flex items-center justify-center px-4 py-12 text-white relative overflow-hidden">
    <!-- Glow Layer -->
    <div class="pointer-events-none fixed inset-0 z-10" :style="glowStyle"></div>

    <!-- Join Cards -->
    <div class="max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-8 z-20">
      <!-- Student Card -->
      <div ref="studentRef"
        class="join-card bg-white/10 backdrop-blur-xl border border-white/20 text-center shadow-lg cursor-pointer"
        :style="[studentStyle, studentHoverStyle]" @mouseenter="isStudentHovered = true"
        @mouseleave="isStudentHovered = false" @click="goToSignup">
        <img src="https://cdn-icons-png.flaticon.com/128/3153/3153024.png" class="w-20 h-20 mx-auto mb-4" />
        <h2 class="text-2xl font-bold text-yellow-300">I'm a Student</h2>
        <p class="text-sm mt-2 text-white/90">Learn, play & grow with fun life skills!</p>
      </div>

      <!-- Parent Card -->
      <div ref="parentRef"
        class="join-card bg-white/10 backdrop-blur-xl border border-white/20 text-center shadow-lg cursor-pointer"
        :style="[parentStyle, parentHoverStyle]" @mouseenter="isParentHovered = true"
        @mouseleave="isParentHovered = false" @click="goToParent">
        <img src="https://cdn-icons-png.flaticon.com/128/2829/2829825.png" class="w-20 h-20 mx-auto mb-4" />
        <h2 class="text-2xl font-bold text-green-300">I'm a Parent</h2>
        <p class="text-sm mt-2 text-white/90">Help guide your child's learning adventure!</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useParallax, useMouse, useElementBounding } from '@vueuse/core'
import { useRouter } from 'vue-router'

const router = useRouter()

// Glow effect
const { x: mouseX, y: mouseY } = useMouse()
const glowStyle = computed(() => ({
  background: `radial-gradient(300px circle at ${mouseX.value}px ${mouseY.value}px, rgba(255, 255, 255, 0.1), transparent 70%)`
}))

// Hover states
const isStudentHovered = ref(false)
const isParentHovered = ref(false)

// Student card
const studentRef = ref(null)
const studentBounds = useElementBounding(studentRef)
const { tilt: tiltS, roll: rollS } = useParallax(studentRef)
const studentStyle = computed(() => ({
  transform: `
    perspective(1000px)
    rotateX(${tiltS.value * 10}deg)
    rotateY(${rollS.value * 10}deg)
  `,
  willChange: 'transform'
}))
const studentHoverStyle = computed(() => ({
  transform: isStudentHovered.value ? 'scale(1.05)' : 'scale(1)',
  transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
}))

// Parent card
const parentRef = ref(null)
const parentBounds = useElementBounding(parentRef)
const { tilt: tiltP, roll: rollP } = useParallax(parentRef)
const parentStyle = computed(() => ({
  transform: `
    perspective(1000px)
    rotateX(${tiltP.value * 10}deg)
    rotateY(${rollP.value * 10}deg)
  `,
  willChange: 'transform'
}))
const parentHoverStyle = computed(() => ({
  transform: isParentHovered.value ? 'scale(1.05)' : 'scale(1)',
  transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)'
}))

// Update bounds on scroll/resize
function updateBounds() {
  studentBounds.update()
  parentBounds.update()
}

onMounted(() => {
  window.addEventListener('scroll', updateBounds)
  window.addEventListener('resize', updateBounds)
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateBounds)
  window.removeEventListener('resize', updateBounds)
})

function goToSignup() {
  router.push('/register')
}
function goToParent() {
  router.push('/register-parent')
}
</script>

<style scoped>
.join-card {
  @apply rounded-2xl p-8 transform-gpu;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}

.pointer-events-none {
  pointer-events: none;
  transition: background 0.1s ease;
  z-index: 0;
}
</style>