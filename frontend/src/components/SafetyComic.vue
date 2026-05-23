<template>
    <!-- Back Button -->
    <router-link to="/safetyskills"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>

    <section class="p-6 max-w-6xl mx-auto text-white">
        <h1 class="text-3xl font-extrabold text-accent mb-3 animate-fade-in">📚 Safety Comics</h1>
        <p class="text-white/70 mb-6 animate-fade-in">
            Learn important safety skills through these engaging comic stories.
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            <div v-for="comic in comics" :key="comic.id"
                class="bg-white/10 backdrop-blur-md rounded-2xl p-4 shadow-card hover:shadow-elevated hover:scale-[1.02] hover:ring-1 hover:ring-accent transition-all cursor-pointer glass-box animate-slide-up"
                @click="goToComic(comic.id)">
                <img :src="comic.thumbnail" :alt="comic.title"
                    class="rounded-xl mb-3 w-full h-40 object-cover shadow-md transition-transform duration-300 hover:scale-[1.02]" />
                <h3 class="text-lg font-bold text-primary-light">{{ comic.title }}</h3>
                <p class="text-sm text-neutral-light mt-1">{{ comic.description }}</p>
            </div>
        </div>
    </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const comics = ref([])

onMounted(async () => {
    try {
        const token = JSON.parse(localStorage.getItem('user'))?.token
        const res = await fetch('/api/v1/safety/comics', {
            headers: {
                Authorization: `Bearer ${token}`,
                'accept': 'application/json',
            },
        })

        const data = await res.json()

        if (data.success && data.data?.comics?.length) {
            comics.value = data.data.comics
        } else {
            comics.value = [] // empty state if no comics
        }
    } catch (e) {
        console.error('⚠ Failed to fetch comics:', e)
        comics.value = []
    }
})

function goToComic(id) {
    router.push({ name: 'safety-comic-view', params: { id } })
}
</script>

<style scoped>
@keyframes fade-in {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slide-up {
    from {
        opacity: 0;
        transform: translateY(30px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-fade-in {
    animation: fade-in 0.8s ease-out both;
}

.animate-slide-up {
    animation: slide-up 0.8s ease-out both;
}

.glass-box {
    @apply border border-white/20;
}

.glass-card {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-4 shadow-lg;
}
</style>
