<template>
  <div class="flex min-h-screen text-white">
    <!-- Sidebar -->
    <Sidebar />

    <!-- Main Content -->
    <div class="flex-1 overflow-y-auto px-4 py-6 flex justify-center items-center">
      <div
        class="max-w-xl w-full bg-white/10 text-white rounded-2xl border border-white/20 backdrop-blur-lg p-8 shadow-card hover:shadow-elevated transition-all duration-300 glass-box hover:ring-1 hover:ring-accent">

        <h2 class="text-3xl font-extrabold text-accent mb-4">🧠 Problem Solving</h2>

        <!-- 🚫 Locked Message -->
        <div v-if="lockedForToday" class="text-center py-8">
          <p class="text-xl font-bold text-yellow-400">🚫 Problem Solving is locked for today!</p>
          <p class="text-white/80 mt-2">Come back tomorrow to solve more problems.</p>
          <p class="mt-4 text-green-400 font-semibold" v-if="badgeEarned">
            🏅 You earned the badge today!
          </p>
        </div>

        <!-- Question Display -->
        <div v-else-if="currentQuestion">
          <p class="text-xl font-semibold mb-6">{{ currentQuestion.question }}</p>

          <!-- Options -->
          <div class="grid gap-4 mb-4">
            <div v-for="(opt, i) in currentQuestion.options" :key="i" @click="selectOption(i)"
              class="bg-white/5 border border-white/10 rounded-xl p-4 cursor-pointer hover:bg-white/10 transition flex items-center justify-between"
              :class="{ 'ring-2 ring-accent': selected === i }">
              <span>{{ opt.text }}</span>
              <span v-if="selected === i">✅</span>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="flex justify-center mb-6">
            <button
              class="px-6 py-2 bg-green-500 hover:bg-green-400 text-white font-semibold rounded-full shadow-md transition"
              @click="submitAnswer" :disabled="selected === null || showExplanation">
              🚀 Submit Answer
            </button>
          </div>

          <!-- Explanation -->
          <div v-if="showExplanation" class="text-center space-y-2">
            <p class="text-xl font-bold" :class="isAnswerCorrect ? 'text-green-400' : 'text-red-400'">
              {{ isAnswerCorrect ? '🎉 Correct!' : '❌ Oops!' }}
            </p>
            <p class="italic text-white/80">💡 Explanation: {{ currentQuestion.explanation }}</p>
            <p class="text-sm text-white">
              Correct Answers: {{ correctAnswers }} / 4 to earn badge 🏅
            </p>

            <!-- Badge Earned -->
            <div v-if="badgeEarned" class="text-green-300 font-semibold mt-2">
              🏅 Badge Earned!
              <router-link to="/profile" class="ml-2 underline text-blue-300 hover:text-blue-200">
                View Profile
              </router-link>
            </div>

            <!-- Next Question -->
            <div class="mt-4" v-if="attempted < 6">
              <button class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-full font-semibold shadow"
                @click="loadNext">
                ➡️ Next Question
              </button>
            </div>
          </div>
        </div>

        <!-- End Message -->
        <div v-else-if="attempted >= 6" class="mt-6 text-center">
          <p class="text-2xl font-bold text-green-400 mb-2">🎉 All Questions Completed!</p>
          <p class="text-white/80 mb-2">✅ Correct: {{ correctAnswers }}</p>
          <p class="text-white/80 mb-2">❌ Incorrect: {{ wrongAnswers }}</p>
          <p class="mt-2 text-yellow-400">🚫 Locked for 24 hours</p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '@/components/SideBar.vue'

const token = localStorage.getItem('firebase_token')

const currentQuestion = ref(null)
const selected = ref(null)

const attempted = ref(0)
const correctAnswers = ref(0)
const wrongAnswers = ref(0)

const badgeEarned = ref(false)
const lockedForToday = ref(false)

const showExplanation = ref(false)
const isAnswerCorrect = ref(false)

// ✅ Fetch one question from API
async function fetchQuestion() {
  try {
    const res = await fetch('/api/v1/problem-solving/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        user_id: "101",   // 🔹 Replace with dynamic user id if needed
        level: "beginner"
      })
    })

    const data = await res.json()
    if (data && data.question) {
      currentQuestion.value = {
        question: data.question,
        options: [
          { text: data.option_a, correct: data.correct_answer === 'A' },
          { text: data.option_b, correct: data.correct_answer === 'B' },
          { text: data.option_c, correct: data.correct_answer === 'C' },
          { text: data.option_d, correct: data.correct_answer === 'D' }
        ],
        explanation: data.explanation
      }
    }
  } catch (err) {
    console.error('❌ Error fetching question', err)
  }
}

// ✅ Submit answer
async function submitAnswer() {
  if (selected.value === null) return

  const chosen = currentQuestion.value.options[selected.value]
  isAnswerCorrect.value = chosen.correct

  attempted.value++
  if (isAnswerCorrect.value) correctAnswers.value++
  else wrongAnswers.value++

  showExplanation.value = true

  // 🏅 Award badge if conditions met
  if (correctAnswers.value >= 4 && !badgeEarned.value) {
    await awardBadge()
    badgeEarned.value = true
  }

  // 🚫 Lock if 6 done
  if (attempted.value >= 6) {
    lockedForToday.value = true
    localStorage.setItem('problemSolvingLock', Date.now())
  }
}

// ✅ Award badge API
async function awardBadge() {
  try {
    await fetch('/api/v1/problem-solving/badges/problem-solving', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` }
    })
    console.log('🏅 Badge awarded!')
  } catch (err) {
    console.error('❌ Error awarding badge', err)
  }
}

// ✅ Next question (fetch new one)
async function loadNext() {
  selected.value = null
  showExplanation.value = false
  await fetchQuestion()
}

// ✅ Select option
function selectOption(index) {
  selected.value = index
}

// ✅ Lock check (24h)
function checkLock() {
  const lastLock = localStorage.getItem('problemSolvingLock')
  if (lastLock) {
    const diff = Date.now() - parseInt(lastLock, 10)
    if (diff < 24 * 60 * 60 * 1000) {
      lockedForToday.value = true
    } else {
      localStorage.removeItem('problemSolvingLock')
    }
  }
}

onMounted(() => {
  checkLock()
  if (!lockedForToday.value) {
    fetchQuestion()
  }
})
</script>

<style scoped>
.glass-box {
  @apply border border-white/20;
}
</style>
