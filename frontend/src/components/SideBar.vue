<template>
    <div :class="[
        'h-full text-white transition-all duration-300 transform-gpu flex flex-col justify-between',
        collapsed ? 'w-16' : 'w-64',
        'bg-white/10 backdrop-blur-xl border-r border-white/20'
    ]">
        <!-- Top Section: Logo + Toggle -->
        <div>
            <div class="flex justify-between items-center px-4 py-4 border-b border-white/20">
                <span v-if="!collapsed" class="text-xl font-extrabold text-accent">Life Skills</span>
                <button @click="collapsed = !collapsed" class="text-white hover:text-accent transition">
                    <span v-if="collapsed">⫷</span>
                    <span v-else>⫸</span>
                </button>
            </div>

            <!-- Navigation Links -->
            <nav class="flex flex-col space-y-2 mt-6 px-2">
                <router-link to="/student-dashboard" class="nav-link">
                    🏠 <span v-if="!collapsed">Dashboard</span>
                </router-link>

                <router-link to="/lifeskills" class="nav-link">
                    📚 <span v-if="!collapsed">Life Skills</span>
                </router-link>

                <router-link to="/dairy" class="nav-link">
                    📓 <span v-if="!collapsed">Dairy</span>
                </router-link>

                <router-link to="/chatbox" class="nav-link">
                    🤖 <span v-if="!collapsed">AI Chat</span>
                </router-link>
            </nav>
        </div>

        <!-- Bottom: Profile Button -->
        <div class="px-2 py-4 border-t border-white/20">
            <router-link to="/profile" class="nav-link justify-center md:justify-start">
                🙍 <span v-if="!collapsed">Profile</span>
            </router-link>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
const collapsed = ref(false)
</script>

<style scoped>
.nav-link {
    @apply flex items-center gap-3 py-2 px-3 rounded-lg transition-all duration-200 font-medium hover:bg-accent/20 hover:text-accent;
}
</style>
  
