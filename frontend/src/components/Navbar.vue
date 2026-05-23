<template>
  <nav
    class="flex items-center justify-between px-6 py-4 bg-primary text-white shadow-xl rounded-b-3xl border-b border-neutral-dark backdrop-blur-md">
    <!-- Logo + Title -->
    <div class="flex items-center gap-3">
      <img src="https://cdn-icons-png.flaticon.com/128/9583/9583795.png"
        class="w-10 h-10 animate-spin-once hover:animate-bounce-once" alt="Life Skills Logo" aria-label="Logo" />
      <h1 class="text-2xl font-extrabold text-accent tracking-wide">Life Skills</h1>
    </div>

    <!-- Links -->
    <ul class="hidden md:flex items-center gap-6 text-base font-semibold">
      <li v-if="!userStore.isLoggedIn">
        <router-link to="/" class="hover:text-accent-light transition-colors">Home</router-link>
      </li>

      <li v-if="userStore.isLoggedIn && userStore.role === 'user'">
        <router-link to="/student-dashboard" class="hover:text-secondary-light transition-colors">
          Dashboard
        </router-link>
      </li>

      <li v-if="userStore.isLoggedIn && userStore.role === 'admin'">
        <router-link to="/admin-skill" class="hover:text-secondary-light transition-colors">
          Admin Panel
        </router-link>
      </li>

      <li v-if="userStore.isLoggedIn && userStore.role === 'parent'">
        <router-link to="/parent-dashboard" class="hover:text-secondary-light transition-colors">
          Parent Dashboard
        </router-link>
      </li>

      <li v-if="userStore.isLoggedIn">
        <button @click="handleLogout" class="text-accent hover:underline hover:text-white transition">
          Logout
        </button>
      </li>
    </ul>
  </nav>
</template>

<script setup>
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'

const router = useRouter()
const userStore = useUserStore()

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
@keyframes spin-once {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes bounce-once {

  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-20%);
  }
}

.animate-spin-once {
  animation: spin-once 1.2s ease-out;
}

.animate-bounce-once {
  animation: bounce-once 0.6s ease-in-out;
}
</style>
