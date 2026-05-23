<template>
    <!-- Back Button -->
    <router-link to="/financeskills"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>

    <div class="flex justify-center items-center min-h-screen px-4">
        <div
            class="max-w-xl w-full bg-white/10 text-white rounded-2xl border border-white/20 backdrop-blur-lg p-8 shadow-card hover:shadow-elevated transition-all duration-300 glass-box hover:ring-1 hover:ring-accent">
            
            <h2 class="text-3xl font-extrabold text-accent mb-4">
                💰 Budget Hero - Level {{ currentLevel }}
            </h2>

            <p class="mb-2 text-lg">
                Your Monthly Income: <span class="font-bold text-primary-light">₹{{ income }}</span>
            </p>
            <p class="mb-6 text-lg">
                Remaining: <span class="font-bold text-green-400">₹{{ remaining }}</span>
            </p>

            <!-- Question Area -->
            <div v-if="currentItem"
                class="bg-white/5 border border-white/10 rounded-2xl p-6 shadow-inner hover:scale-[1.01] transition">
                <p class="text-xl font-semibold mb-2">
                    Spend <span class="text-yellow-300 font-bold">₹{{ currentItem.cost }}</span> on
                    <span class="italic text-white">"{{ currentItem.name }}"</span>?
                </p>
                <p class="text-white/70 text-sm mb-4">{{ currentItem.description }}</p>

                <div class="mt-4 flex justify-center gap-6">
                    <button @click="handleChoice(true)"
                        class="px-6 py-2 bg-green-500 hover:bg-green-400 text-white font-semibold rounded-full shadow-md transition-all">
                        ✅ Yes
                    </button>
                    <button @click="handleChoice(false)"
                        class="px-6 py-2 bg-red-500 hover:bg-red-400 text-white font-semibold rounded-full shadow-md transition-all">
                        ❌ No
                    </button>
                </div>
            </div>

            <!-- Level Complete Area -->
            <div v-else class="mt-8 text-center">
                <p class="text-2xl font-bold text-green-400 mb-3">
                    🎉 Level {{ currentLevel }} Completed!
                </p>
                <p class="mb-1 text-white/80">✅ Needs Covered: 
                    <span class="font-semibold text-white">{{ score.needs }}</span>
                </p>
                <p class="mb-1 text-white/80">🚫 Wants Skipped: 
                    <span class="font-semibold text-white">{{ score.wants }}</span>
                </p>
                <p class="mt-3 text-lg font-bold text-accent-light">
                    🧠 Final Score: 
                    <span class="text-yellow-300">{{ finalScore }} / {{ items.length }}</span>
                </p>

                <div class="mt-6 flex flex-col sm:flex-row justify-center gap-4">
                    <button v-if="!nextLevelAvailable" disabled
                        class="px-6 py-2 bg-gray-500 text-white rounded-full font-semibold">
                        🚧 More levels coming soon
                    </button>
                    <button v-else @click="goToNextLevel"
                        class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-semibold shadow">
                        🔓 Go to Level {{ currentLevel + 1 }}
                    </button>
                    <button @click="resetGame"
                        class="px-6 py-2 bg-yellow-500 hover:bg-yellow-400 text-black rounded-full font-semibold">
                        🔄 Retry
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const income = ref(0)
const remaining = ref(0)
const items = ref([])
const currentItem = ref(null)
const index = ref(0)
const currentLevel = ref(1)
const maxLevel = ref(1) // will be updated dynamically if backend provides info
const score = ref({ needs: 0, wants: 0 })

const finalScore = computed(() => score.value.needs + score.value.wants)
const nextLevelAvailable = computed(() => currentLevel.value < maxLevel.value)

function handleChoice(accepted) {
    const item = currentItem.value
    if (accepted && remaining.value >= item.cost) {
        remaining.value -= item.cost
        if (item.item_type === 'need') score.value.needs++
    } else if (!accepted && item.item_type === 'want') {
        score.value.wants++
    }
    index.value++
    currentItem.value = items.value[index.value] || null
}

function resetGame() {
    remaining.value = income.value
    score.value = { needs: 0, wants: 0 }
    index.value = 0
    currentItem.value = items.value[0] || null
}

function goToNextLevel() {
    currentLevel.value++
    fetchGameLevel(currentLevel.value)
}

async function fetchGameLevel(level) {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch(`/api/v1/finance/game/level/${level}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (!res.ok || !data.success) throw new Error(data.message || 'Backend Error')

        income.value = data.data.income
        items.value = data.data.items || []
        remaining.value = income.value
        score.value = { needs: 0, wants: 0 }
        index.value = 0
        currentItem.value = items.value[0] || null
    } catch (err) {
        console.error('❌ Error fetching game level:', err.message)
        items.value = []
        currentItem.value = null
    }
}

onMounted(() => fetchGameLevel(currentLevel.value))
</script>

<style scoped>
.glass-card {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-4 shadow-lg;
}
@keyframes fade-in {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in { animation: fade-in 0.8s ease-out both; }
.glass-box { @apply border border-white/20; }
</style>
