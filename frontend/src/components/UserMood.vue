<template>
    <div class="glass-box">
        <h2 class="text-2xl font-bold text-accent mb-4">📓 Child Mood & Diary</h2>

        <!-- Child Selector -->
        <div v-if="children.length" class="mb-4">
            <label class="mr-2 text-lg font-medium">Select Child:</label>
            <select v-model="selectedChild" @change="fetchDiary" class="px-4 py-2 rounded-lg text-black">
                <option v-for="child in children" :key="child.id" :value="child.id">
                    {{ child.first_name }}
                </option>
            </select>
        </div>
        <p v-else class="text-gray-400">⚠️ No children found.</p>

        <!-- Mood Trend Chart -->
        <div v-if="moodTrend.labels.length" class="h-64 mb-6">
            <LineChart :data="chartData" :options="chartOptions" />
        </div>

        <!-- Supportive Tips -->
        <div v-if="supportiveTip" class="glass-box bg-green-900/40 p-4 mb-6">
            <h3 class="text-lg font-semibold text-green-300">💡 Supportive Tip</h3>
            <p class="mt-2 text-gray-100">{{ supportiveTip }}</p>
        </div>

        <!-- Diary Entries -->
        <div v-if="entries.length" class="space-y-4">
            <div v-for="entry in entries" :key="entry.id" class="bg-white/10 p-4 rounded-lg shadow-md">
                <p class="text-sm text-gray-300">
                    {{ formatDate(entry.date) }} | Mood: {{ entry.mood }}/10
                </p>
                <p class="mt-2">{{ entry.text }}</p>
            </div>
        </div>
        <p v-else class="text-gray-400">No diary entries found.</p>
    </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from "vue";
import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
} from "chart.js";
import { Line as LineChart } from "vue-chartjs";

// ✅ Register chart.js components
ChartJS.register(
    Title,
    Tooltip,
    Legend,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale
);

// state
const children = ref([]);
const selectedChild = ref(null);
const entries = ref([]);
const moodTrend = reactive({
    labels: [],
    values: [],
});
const supportiveTip = ref("");

// token
const token = localStorage.getItem("firebase_token");

// Fetch children
async function fetchChildren() {
    try {
        const res = await fetch("/api/v1/parent/children", {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (data.success) {
            children.value = data.data.children || [];
            if (children.value.length > 0) {
                selectedChild.value = children.value[0].id;
                fetchDiary();
            }
        }
    } catch (err) {
        console.error("❌ Failed to fetch children", err);
    }
}

// Fetch diary for selected child
async function fetchDiary() {
    if (!selectedChild.value) return;
    try {
        const res = await fetch(
            `/api/v1/parent/child/${selectedChild.value}/diary`,
            {
                headers: { Authorization: `Bearer ${token}` },
            }
        );
        const data = await res.json();
        if (data.success) {
            entries.value = data.data.entries || [];
            computeMoodTrend();
            fetchSupportiveTip(); // 🔑 Call AI tip after entries are fetched
        }
    } catch (err) {
        console.error("❌ Failed to fetch diary", err);
    }
}

// Compute mood trend from diary entries
function computeMoodTrend() {
    const grouped = {};
    entries.value.forEach((e) => {
        if (!grouped[e.date]) grouped[e.date] = [];
        grouped[e.date].push(e.mood);
    });

    moodTrend.labels = Object.keys(grouped).sort();
    moodTrend.values = moodTrend.labels.map(
        (date) => grouped[date].reduce((sum, m) => sum + m, 0) / grouped[date].length
    );
}

// Fetch supportive tip from AI API
async function fetchSupportiveTip() {
    if (!entries.value.length) return;
    try {
        const res = await fetch("/api/v1/ai/supportive-tips", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ entries: entries.value }),
        });

        const data = await res.json();
        if (data.success) {
            supportiveTip.value = data.data.tip;
        } else {
            supportiveTip.value = "⚠️ No supportive tip available.";
        }
    } catch (err) {
        console.error("❌ Failed to fetch supportive tip", err);
        supportiveTip.value = "❌ Could not generate a supportive tip.";
    }
}

// Chart.js computed data
const chartData = computed(() => ({
    labels: moodTrend.labels,
    datasets: [
        {
            label: "Average Mood",
            data: moodTrend.values,
            borderColor: "#4ade80",
            backgroundColor: "rgba(74, 222, 128, 0.2)",
            tension: 0.3,
            fill: true,
        },
    ],
}));

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        y: {
            min: 0,
            max: 10,
            ticks: { stepSize: 1 },
        },
    },
};

// Format date nicely
function formatDate(dateStr) {
    return new Date(dateStr).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

onMounted(() => {
    fetchChildren();
});
</script>

<style scoped>
.glass-box {
    @apply bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 shadow-lg;
}
</style>
