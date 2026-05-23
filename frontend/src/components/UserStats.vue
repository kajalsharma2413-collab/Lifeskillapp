<template>
    <div class="space-y-8">
        <!-- Profile Header -->
        <div class="flex items-center gap-4">
            <img :src="profile?.avatar_url || '/default-avatar.png'" alt="avatar"
                class="w-16 h-16 rounded-full border-2 border-accent shadow-md" />
            <div>
                <h2 class="text-2xl font-bold text-accent">
                    {{ profile?.first_name }} {{ profile?.last_name }}
                </h2>
                <p class="text-gray-300">@{{ profile?.username }}</p>
            </div>
        </div>

        <!-- Stats Grid -->
        <div v-if="statCards.length" class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div v-for="card in statCards" :key="card.label" class="glass-box text-center p-4">
                <p class="text-2xl font-bold text-accent">{{ card.value }}</p>
                <p class="text-gray-300">{{ card.label }}</p>
            </div>
        </div>
        <p v-else class="text-gray-400 text-center">⚠️ No stats available</p>

        <!-- Profile Completion -->
        <div class="glass-box flex flex-col items-center p-6">
            <h3 class="text-lg font-semibold text-accent mb-2">
                Profile Completion
            </h3>
            <div class="relative w-40 h-40">
                <svg class="w-full h-full transform -rotate-90">
                    <circle cx="80" cy="80" r="70" stroke="gray" stroke-width="12" fill="transparent" />
                    <circle cx="80" cy="80" r="70" stroke="url(#grad)" stroke-width="12" fill="transparent"
                        stroke-linecap="round" :stroke-dasharray="circumference" :stroke-dashoffset="circumference - (profileCompletion / 100) * circumference
                            " />
                    <defs>
                        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="#38bdf8" />
                            <stop offset="100%" stop-color="#a855f7" />
                        </linearGradient>
                    </defs>
                </svg>
                <div class="absolute inset-0 flex items-center justify-center">
                    <span class="text-2xl font-bold text-accent">
                        {{ profileCompletion.toFixed(1) }}%
                    </span>
                </div>
            </div>
        </div>

        <!-- Last Activity -->
        <div v-if="stats?.last_activity" class="glass-box text-center p-4">
            <p class="text-gray-300">📅 Last Activity</p>
            <p class="text-lg font-semibold text-accent">
                {{ formatDate(stats.last_activity) }}
            </p>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from "vue"

const props = defineProps({
    child: { type: Object, required: true },
})

const token = localStorage.getItem("firebase_token")

const profile = ref(null)
const stats = ref(null)

const circumference = 2 * Math.PI * 70
const profileCompletion = ref(0)
const statCards = ref([])

// 🔄 Watch for child change
watch(
    () => props.child,
    (newChild) => {
        if (newChild?.id) {
            fetchProfile(newChild.id)
            fetchStats(newChild.id)
        } else {
            profile.value = null
            stats.value = null
            statCards.value = []
            profileCompletion.value = 0
        }
    },
    { immediate: true }
)

// Fetch profile API
async function fetchProfile(userId) {
    try {
        const res = await fetch(`/api/v1/users/profile/${userId}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (data.success) {
            profile.value = data.data.user
        }
    } catch (err) {
        console.error("❌ Failed to fetch profile", err)
    }
}

// Fetch stats API
async function fetchStats(userId) {
    try {
        const res = await fetch(`/api/v1/users/stats/${userId}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (data.success) {
            stats.value = data.data.stats
            profileCompletion.value = stats.value.profile_completion || 0
            statCards.value = [
                { label: "Points", value: stats.value.points ?? 0 },
                { label: "Badges", value: stats.value.badges_count ?? 0 },
                { label: "Current Skills", value: stats.value.current_skills_count ?? 0 },
                { label: "Completed Skills", value: stats.value.completed_skills_count ?? 0 },
                { label: "Account Age (days)", value: stats.value.account_age_days ?? 0 },
            ]
        }
    } catch (err) {
        console.error("❌ Failed to fetch stats", err)
    }
}

// Date formatter
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleString()
}
</script>

<style scoped>
.glass-box {
    @apply bg-white/10 backdrop-blur-md border border-white/20 rounded-xl shadow-lg;
}
</style>
