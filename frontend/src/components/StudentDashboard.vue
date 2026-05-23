<template>
    <div class="flex min-h-screen text-white">
        <!-- Sidebar -->
        <Sidebar />

        <!-- Main Content -->
        <div class="flex-1 p-6 overflow-y-auto space-y-10">
            <!-- Welcome -->
            <h1 class="text-4xl font-bold animate-fade-in text-accent">
                👋 Welcome, {{ name }}!
            </h1>

            <!-- Stats Cards -->
            <section>
                <h2 class="text-2xl font-semibold mb-4 animate-slide-in-left text-secondary-light">
                    📊 Your Stats
                </h2>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div v-for="(value, key) in displayStats" :key="key"
                        class="glass-box animate-scale-up text-center p-6">
                        <h3 class="text-lg font-semibold capitalize text-accent">
                            {{ formatKey(key) }}
                        </h3>
                        <p class="text-2xl font-bold text-white mt-2">
                            {{ value }}
                        </p>
                    </div>
                </div>
            </section>

            <!-- Motivational Quote -->
            <section class="glass-box animate-fade-in">
                <h2 class="text-2xl font-semibold mb-3 animate-slide-in-left text-white">
                    💬 Daily Motivation
                </h2>
                <div class="text-lg font-semibold italic text-center text-white/90">
                    "{{ quote }}"
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import Sidebar from "@/components/SideBar.vue";

const name = ref("");
const quote = ref("");
const stats = ref({});

// ✅ remove last_activity
const displayStats = computed(() => {
    const { last_activity, ...rest } = stats.value || {};
    return rest;
});

function formatKey(key) {
    return key
        .replace(/_/g, " ") // replace underscores
        .replace(/\b\w/g, (c) => c.toUpperCase()); // capitalize words
}

async function fetchQuote() {
    try {
        const proxyUrl = "https://api.allorigins.win/get?url=";
        const apiUrl = encodeURIComponent("https://zenquotes.io/api/random");
        const response = await fetch(`${proxyUrl}${apiUrl}`);
        if (!response.ok) throw new Error("Failed to fetch quote.");

        const data = await response.json();
        const parsed = JSON.parse(data.contents);
        const quoteText = parsed[0]?.q?.trim() || "Keep going.";
        const author = parsed[0]?.a?.trim() || "Unknown";
        quote.value = `${quoteText} — ${author}`;
    } catch (err) {
        console.error("Quote fetch error:", err);
        quote.value =
            "Judge your success by what you had to give up in order to get it — Dalai Lama";
    }
}

async function fetchMyStats() {
    try {
        const token = JSON.parse(localStorage.getItem("user"))?.token;
        const res = await fetch("/api/v1/users/my-stats", {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();

        if (data.success && data.data?.stats) {
            stats.value = data.data.stats;
            name.value = JSON.parse(localStorage.getItem("user"))?.name || "Student";
        }
    } catch (err) {
        console.error("My Stats fetch error:", err);
    }
}

onMounted(() => {
    fetchQuote();
    fetchMyStats();
});
</script>

<style scoped>
@keyframes fade-in {
    from {
        opacity: 0;
        transform: translateY(10px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slide-in-left {
    from {
        transform: translateX(-20px);
        opacity: 0;
    }

    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes scale-up {
    from {
        transform: scale(0.95);
    }

    to {
        transform: scale(1);
    }
}

.animate-fade-in {
    animation: fade-in 0.8s ease-out forwards;
}

.animate-slide-in-left {
    animation: slide-in-left 0.8s ease-out forwards;
}

.animate-scale-up {
    animation: scale-up 0.5s ease-out forwards;
}

.glass-box {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 p-6 rounded-xl shadow-md;
}
</style>
