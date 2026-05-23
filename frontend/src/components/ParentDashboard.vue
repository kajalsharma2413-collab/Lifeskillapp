<template>
  <div class="max-w-6xl mx-auto py-10 px-6 text-white space-y-10">
    <h2 class="text-4xl font-bold text-center text-accent">👨‍👧 Parent Dashboard</h2>

    <!-- Generate Parent Code -->
    <div class="text-center space-y-4">
      <button @click="generateParentCode"
        class="py-2 px-6 rounded-full border border-accent text-accent hover:bg-accent-light hover:text-black transition">
        🧬 Generate Parent Code
      </button>

      <div v-if="parentCode" class="flex justify-center items-center gap-3">
        <span class="bg-white text-black font-mono px-4 py-2 rounded-lg shadow-md">
          {{ parentCode }}
        </span>
        <button @click="copyToClipboard" class="hover:text-accent text-xl" title="Copy to clipboard">
          📋
        </button>
      </div>
    </div>

    <!-- Child Selector -->
    <div v-if="children.length" class="text-center mt-4">
      <label for="child-select" class="text-lg font-medium text-accent mr-2">
        Viewing data for:
      </label>
      <select id="child-select" v-model="selectedChild" class="text-black px-4 py-2 rounded-xl">
        <option v-for="child in children" :key="child.id" :value="child">
          {{ child.first_name }} (Age: {{ child.age }})
        </option>
      </select>
    </div>
    <p v-else class="text-gray-400 text-center mt-4">⚠️ No children linked to this parent</p>

    <!-- Tabs -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <button @click="activeTab = 'stats'" :class="btnClass('stats')">📊 User Stats</button>
      <button @click="activeTab = 'mood'" :class="btnClass('mood')">📓 User Mood</button>
    </div>

    <!-- Tab Content -->
    <div v-if="activeTab === 'stats'" class="glass-box">
      <UserStats v-if="selectedChild" :child="selectedChild" />
      <p v-else class="text-gray-400">⚠️ No child selected</p>
    </div>

    <div v-if="activeTab === 'mood'" class="glass-box">
      <UserMood v-if="selectedChild" :child="selectedChild" />
      <p v-else class="text-gray-400">⚠️ No child selected</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import UserMood from "./UserMood.vue"
import UserStats from "./UserStats.vue"

const activeTab = ref("stats")
const parentCode = ref("")
const children = ref([])
const selectedChild = ref(null)

const token = localStorage.getItem("firebase_token")

// API: Generate Parent Code
async function generateParentCode() {
  try {
    const res = await fetch("/api/v1/auth/generate-parent-code", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await res.json()
    parentCode.value = data?.data?.code || "N/A"
  } catch (err) {
    console.error("❌ Failed to generate code", err)
    alert("❌ Failed to generate code")
  }
}

// Copy to clipboard
function copyToClipboard() {
  navigator.clipboard.writeText(parentCode.value)
  alert("📋 Copied to clipboard!")
}

// ✅ API: Fetch children directly from /api/v1/parent/children
async function fetchChildren() {
  try {
    const res = await fetch("/api/v1/parent/children", {
      headers: { Authorization: `Bearer ${token}` },
    })
    const data = await res.json()
    if (data.success) {
      children.value = data.data.children || []
      selectedChild.value = children.value[0] || null
    }
  } catch (err) {
    console.error("❌ Failed to fetch children", err)
  }
}

// Button class styling
function btnClass(tab) {
  return `py-3 px-6 rounded-xl border font-semibold text-center transition duration-300 ${activeTab.value === tab
      ? "bg-accent text-black"
      : "border-accent text-accent hover:bg-accent-light hover:text-black"
    }`
}

onMounted(() => {
  fetchChildren()
})
</script>

<style scoped>
.glass-box {
  @apply bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 shadow-lg;
}
</style>
