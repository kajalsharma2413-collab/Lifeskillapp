<template>
    <!-- Back Button -->
    <router-link to="/safetyskills"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>
    <section class="p-6 max-w-6xl mx-auto text-white">
        <h1 class="text-3xl font-extrabold text-accent mb-3 animate-fade-in">📺 Safety Skill Videos</h1>
        <p class="text-white/70 mb-6 animate-fade-in">Watch these short videos to learn how to stay safe in emergencies.
        </p>

        <div v-if="videos.length" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            <div v-for="video in videos" :key="video.id"
                class="bg-white/10 backdrop-blur-md rounded-2xl p-4 shadow-card hover:shadow-elevated hover:scale-[1.02] hover:ring-1 hover:ring-accent transition-all cursor-pointer glass-box animate-slide-up"
                @click="goToVideo(video.id)">
                <img :src="video.thumbnail" :alt="video.title"
                    class="rounded-xl mb-3 w-full h-40 object-cover shadow-md transition-transform duration-300 hover:scale-[1.02]" />
                <h3 class="text-lg font-bold text-primary-light">{{ video.title }}</h3>
                <p class="text-sm text-neutral-light mt-1">{{ video.description }}</p>
            </div>
        </div>

        <div v-else class="text-white/60 mt-6 text-center">
            No videos available at the moment.
        </div>
    </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const videos = ref([])

onMounted(async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        if (!token) throw new Error('No Firebase token found')

        const res = await fetch('/api/v1/safety/videos', {
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`,
            },
        })

        if (!res.ok) throw new Error(`API error: ${res.status}`)

        const data = await res.json()
        if (data.success && data.data?.videos?.length) {
            videos.value = data.data.videos
        } else {
            throw new Error('Empty video list')
        }
    } catch (e) {
        console.error('❌ Failed to fetch videos:', e)
    }
})

function goToVideo(id) {
    router.push({ name: 'safety-video-view', params: { id } })
}
</script>

<style scoped>
.glass-card {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-4 shadow-lg;
}
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
</style>
