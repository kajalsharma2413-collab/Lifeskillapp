<template>
    <section class="max-w-4xl mx-auto p-6 text-white">
        <div ref="card" :style="cardStyle" class="glass-box animate-fade-in">
            <!-- Quiz Questions -->
            <div v-if="questions.length && !showScore">
                <div class="text-sm text-white/70 mb-3 font-medium">
                    Question {{ currentIndex + 1 }} of {{ questions.length }}
                </div>

                <div class="w-full bg-white/20 rounded-full h-2 mb-4">
                    <div class="bg-accent h-2 rounded-full"
                        :style="{ width: ((currentIndex + 1) / questions.length) * 100 + '%' }"></div>
                </div>

                <h2 class="text-xl font-extrabold text-yellow-300 mb-4 text-center">
                    {{ questions[currentIndex].question_text }}
                </h2>

                <ul class="space-y-3 mb-6">
                    <li v-for="option in questions[currentIndex].options" :key="option.id"
                        class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/10 cursor-pointer hover:bg-white/10 transition"
                        @click="selectedAnswer = option.id">
                        <input type="radio" :id="option.id" :value="option.id" v-model="selectedAnswer"
                            class="accent-accent cursor-pointer" />
                        <label :for="option.id" class="text-white/90 cursor-pointer w-full">{{ option.text }}</label>
                    </li>
                </ul>

                <div class="flex justify-between items-center">
                    <button
                        class="px-4 py-2 rounded-full bg-white/10 border border-white/20 text-white hover:bg-white/20 transition"
                        :disabled="currentIndex === 0" @click="prevQuestion">
                        ⬅ Previous
                    </button>

                    <button
                        class="px-6 py-2 rounded-full bg-accent text-black font-bold hover:bg-accent-light transition"
                        @click="submitAnswer">
                        ✅ Submit Answer
                    </button>

                    <button
                        class="px-4 py-2 rounded-full bg-white/10 border border-white/20 text-white hover:bg-white/20 transition"
                        :disabled="currentIndex >= questions.length - 1" @click="nextQuestion">
                        Next ➡
                    </button>
                </div>
            </div>

            <!-- No Quiz -->
            <div v-else-if="!questions.length && !showScore" class="text-center py-12">
                <h2 class="text-xl font-bold text-red-300">🛑 Quiz Not Available</h2>
                <p class="text-white/70">We couldn’t load the quiz. Please try again later.</p>
            </div>

            <!-- Score Section -->
            <div v-if="showScore" class="mt-10 text-center space-y-4">
                <h3 class="text-2xl font-bold text-yellow-300">🎯 Your Score</h3>
                <p class="text-white text-xl">{{ score }}%</p>

                <div v-if="passed">
                    <router-link to="/profile"
                        class="inline-block px-6 py-2 mt-2 rounded-full bg-green-500 text-white font-semibold hover:bg-green-600 transition">
                        🏅 Check Your New Badge
                    </router-link>
                </div>

                <div v-else>
                    <button
                        class="px-6 py-2 mt-2 rounded-full bg-red-500 text-white font-semibold hover:bg-red-600 transition"
                        @click="retryQuiz">
                        🔁 Try Again to Earn Your Badge
                    </button>
                </div>
            </div>
        </div>
    </section>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useParallax } from '@vueuse/core'

const route = useRoute()
const videoId = route.params.id

const questions = ref([])
const currentIndex = ref(0)
const selectedAnswer = ref(null)
const answers = ref([]) // store all answers
const showScore = ref(false)
const score = ref(0)
const passed = ref(false)
const minScore = ref(50)

onMounted(async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch(`/api/v1/quiz/video/${videoId}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        if (!res.ok) throw new Error('Failed to load quiz')
        const data = await res.json()
        questions.value = data.data.questions
        minScore.value = data.data.metadata.min_score || 50
    } catch (err) {
        console.error('⚠️ Failed to fetch quiz:', err.message)
    }
})

const submitAnswer = () => {
    if (!selectedAnswer.value) return
    answers.value.push({
        question_id: questions.value[currentIndex.value].id,
        selected_option_id: selectedAnswer.value
    })
    nextQuestion()
}

const nextQuestion = () => {
    if (currentIndex.value < questions.value.length - 1) {
        currentIndex.value++
        selectedAnswer.value = null
    } else {
        finishQuiz()
    }
}

const prevQuestion = () => {
    if (currentIndex.value > 0) {
        currentIndex.value--
        selectedAnswer.value = null
    }
}

const finishQuiz = async () => {
    const token = localStorage.getItem('firebase_token')
    try {
        const res = await fetch(`/api/v1/safety/video/${videoId}/quiz/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                answers: answers.value,
                time_taken_seconds: 0
            })
        })
        if (!res.ok) throw new Error('Failed to submit quiz')
        const data = await res.json()

        score.value = data.data.score_percentage
        passed.value = data.data.passed
        showScore.value = true
    } catch (err) {
        alert('Error submitting quiz: ' + err.message)
    }
}

const retryQuiz = () => {
    currentIndex.value = 0
    selectedAnswer.value = null
    answers.value = []
    showScore.value = false
    score.value = 0
    passed.value = false
}

const card = ref(null)
const { tilt, roll } = useParallax(card)
const cardStyle = computed(() => ({
    transform: `perspective(1000px) rotateX(${tilt.value * 5}deg) rotateY(${roll.value * 5}deg)`,
    transition: 'transform 0.2s ease-out',
    'will-change': 'transform',
}))
</script>

<style scoped>
@keyframes fade-in {
    from {
        opacity: 0;
        transform: translateY(15px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.animate-fade-in {
    animation: fade-in 0.8s ease-out both;
}
.glass-box {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 p-6 rounded-xl shadow-lg;
}
</style>
