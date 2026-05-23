<script setup>
import { ref, onMounted, computed } from 'vue'
import SideBar from '@/components/SideBar.vue'
import MentorChatbot from './MentorChatbot.vue'

// States
const entry = ref('')
const feedback = ref(null)
const recentEntries = ref([])
const loading = ref(false)

// Current timestamp → default to today at 20:00
const now = new Date()
now.setHours(20, 0, 0, 0) // always default at 20:00
const timestamp = ref(now.toISOString().slice(0, 16))

// Mentor session states
const mentorSession = ref(null)
const showChatbot = ref(false)

// Dates already used in recent entries
const usedDates = computed(() =>
    recentEntries.value.map(e => new Date(e.date).toISOString().slice(0, 10))
)

// Restrict min and max date (only last 7 days)
const minDate = new Date()
minDate.setDate(new Date().getDate() - 7)
const maxDate = new Date()

const minDateStr = minDate.toISOString().slice(0, 10)
const maxDateStr = maxDate.toISOString().slice(0, 10)

// Get mood and emoji from score
const getMoodAndEmoji = (score) => {
    if (score >= 7) return { mood: 'Happy', emoji: '😊' }
    if (score > 3 && score < 7) return { mood: 'Normal', emoji: '😐' }
    return { mood: 'Sad', emoji: '😢' }
}

const analyzeEntry = async () => {
    if (!entry.value.trim()) return alert('Please write something first.')
    
    if (entry.value.trim().length < 70) {
        return alert('✍️ Please write at least 70 characters to reflect on your day.')
    }

    loading.value = true
    try {
        const token = localStorage.getItem('firebase_token')
        const firebaseUser = JSON.parse(localStorage.getItem('firebase_user') || '{}')

        // 1️⃣ Analyze diary entry first
        const analyzeRes = await fetch('/api/v1/diary/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({ diary_entry: entry.value })
        })
        const analyzeData = await analyzeRes.json()

        if (analyzeData.summary && analyzeData.score !== undefined) {
            feedback.value = analyzeData

            // Derive mood & emoji
            const { mood, emoji } = getMoodAndEmoji(analyzeData.score)

            // 2️⃣ Save diary entry (schema required by backend)
            await fetch('/api/v1/diary/entry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({
                    user_id: firebaseUser?.uid,
                    entry_text: entry.value,
                    mood,
                    emoji,
                    ai_response: analyzeData.summary,
                    timestamp: new Date(timestamp.value).toISOString()
                })
            })

            fetchRecentEntries()
        } else {
            alert('⚠️ AI could not analyze your entry. Please try again.')
        }
    } catch (err) {
        console.error(err)
        alert('❌ Failed to analyze entry')
    } finally {
        loading.value = false
    }
}

const fetchRecentEntries = async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch('/api/v1/diary/entries?limit=7', {
            headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()

        if (data.success && data.data) {
            recentEntries.value = data.data.entries || []
        }
    } catch (err) {
        console.error('❌ Failed to fetch recent entries', err)
    }
}

const initMentor = async (entryText) => {
    try {
        const token = localStorage.getItem('firebase_token')
        const firebaseUser = JSON.parse(localStorage.getItem('firebase_user') || '{}')

        // user_name and age are required by the backend schema
        const userName = firebaseUser?.displayName || firebaseUser?.email?.split('@')[0] || 'Friend'
        const userAge = firebaseUser?.age || 12 // sensible default; update if age is stored elsewhere

        const res = await fetch('/api/v1/mentor/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                user_name: userName,
                age: userAge,
                current_diary_entry: entryText
            })
        })
        const data = await res.json()

        if (res.ok && data.session_id) {
            mentorSession.value = data
            showChatbot.value = true
        } else {
            alert('⚠️ Failed to start mentor session')
        }
    } catch (err) {
        console.error('❌ Mentor init error', err)
    }
}

onMounted(() => {
    fetchRecentEntries()
})
</script>

<template>
    <div class="flex min-h-screen text-white">
        <!-- Sidebar -->
        <SideBar />

        <!-- Main Content -->
        <div class="flex-1 overflow-y-auto px-4 py-6">
            <div class="min-h-screen flex items-center justify-center px-4 py-10">
                <div class="w-full max-w-2xl text-white space-y-8">

                    <!-- ✏️ Diary Input Glass Card -->
                    <div class="bg-white/10 backdrop-blur-xl p-8 rounded-3xl border border-white/20 shadow-2xl">
                        <h1 class="text-3xl font-bold mb-6 text-accent">📝 Daily Reflection</h1>

                        <!-- Diary Text -->
                        <textarea v-model="entry" placeholder="How did your day go?"
                            class="w-full p-4 rounded-lg border border-white/20 text-white bg-white/5 placeholder-white/70 resize-none focus:outline-none focus:ring-2 focus:ring-accent"
                            rows="5" />

                        <!-- Timestamp Picker -->
                        <div class="mt-4">
                            <label for="timestamp" class="block mb-2 text-white/80">🗓 Choose Timestamp</label>
                            <input type="datetime-local" id="timestamp" v-model="timestamp" :min="minDateStr + 'T00:00'"
                                :max="maxDateStr + 'T23:59'"
                                class="w-full p-2 rounded-lg border border-white/30 bg-white/20 text-white focus:ring-2 focus:ring-accent focus:outline-none" />
                            <p v-if="usedDates.includes(timestamp.slice(0, 10))" class="text-red-400 text-sm mt-1">
                                ⚠️ You already wrote an entry for this date. Please choose another.
                            </p>
                        </div>

                        <div class="mt-6 text-right">
                            <button @click="analyzeEntry"
                                :disabled="loading || usedDates.includes(timestamp.slice(0, 10))"
                                class="px-6 py-2 bg-accent hover:bg-accent-light text-white rounded-full font-semibold transition duration-300 disabled:opacity-50">
                                {{ loading ? 'Analyzing...' : '✨ Analyze My Day' }}
                            </button>
                        </div>

                        <!-- AI Feedback -->
                        <div v-if="feedback" class="mt-10 bg-white/10 border border-white/20 p-6 rounded-2xl">
                            <h2 class="text-2xl font-bold text-accent mb-4">🤖 AI Feedback</h2>

                            <div class="mb-4">
                                <h3 class="text-lg font-semibold mb-1">📄 Summary</h3>
                                <p class="text-white/90">{{ feedback.summary }}</p>
                            </div>

                            <div>
                                <h3 class="text-lg font-semibold mb-1">📊 Mood-Score</h3>
                                <p class="text-white/80">
                                    {{ getMoodAndEmoji(feedback.score).mood }} {{ getMoodAndEmoji(feedback.score).emoji
                                    }}
                                    — {{ feedback.score }}/10
                                </p>
                            </div>
                        </div>
                    </div>

                    <!-- 🗓 Recent Entries Glass Card -->
                    <div v-if="recentEntries.length"
                        class="bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl p-6 rounded-3xl">
                        <h2 class="text-xl font-bold text-accent mb-4">📅 Your Recent Entries</h2>
                        <ul class="space-y-3">
                            <li v-for="(item, index) in recentEntries" :key="item.id"
                                class="bg-white/5 border border-white/10 p-4 rounded-lg flex justify-between items-start">

                                <!-- Entry Content -->
                                <div class="flex-1">
                                    <p class="text-white/90 mb-2">📝 {{ item.text }}</p>
                                    <p class="text-sm text-white/70 italic mb-2">🤖 {{ item.ai_summary }}</p>
                                    <small class="text-white/60 block">
                                        {{ item.mood_category }} {{ item.emoji }} — Score: {{ item.wellbeing_score }}/10
                                        <br />
                                        📅 {{ new Date(item.date).toLocaleDateString() }}
                                    </small>
                                </div>

                                <!-- 👨‍🏫 Mentor Button -->
                                <button @click="initMentor(item.text)" title="💡 Ask mentor about this day"
                                    class="ml-3 text-2xl hover:scale-110 transition-transform">
                                    👨‍🏫
                                </button>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Mentor Chatbot -->
        <MentorChatbot v-if="mentorSession" :session="mentorSession" :show="showChatbot" @close="showChatbot = false" />
    </div>
</template>

<style scoped>
.bg-accent {
    @apply bg-purple-600;
}

.bg-accent-light {
    @apply bg-purple-500;
}

.text-accent {
    @apply text-purple-300;
}
</style>
