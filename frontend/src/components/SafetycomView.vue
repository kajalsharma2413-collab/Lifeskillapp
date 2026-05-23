<template>
    <!-- Back Button -->
    <router-link to="/safetycomic"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>

    <section class="max-w-4xl mx-auto p-6 text-white">
        <div v-if="comic" class="animate-fade-in">
            <h2 class="text-3xl font-extrabold text-accent mb-6">📖 {{ comic.title }}</h2>

            <!-- PDF Viewer -->
            <div class="w-full h-[70vh] bg-black rounded-xl overflow-hidden shadow-xl mb-6">
                <VuePdfApp v-if="src" :pdf="src" />
            </div>

            <!-- Description -->
            <p class="text-lg text-neutral-light text-center mb-6">{{ comic.description }}</p>

            <!-- Like/Dislike -->
            <div class="flex items-center justify-center gap-10 mb-6">
                <button @click="toggleLike" class="flex items-center gap-1 text-lg transition"
                    :class="liked ? 'text-green-400 font-bold' : 'hover:text-green-400 text-white/70'">
                    <span>{{ liked ? '👍' : '👍🏻' }}</span>
                    <span>{{ likes }}</span>
                </button>

                <button @click="toggleDislike" class="flex items-center gap-1 text-lg transition"
                    :class="disliked ? 'text-red-400 font-bold' : 'hover:text-red-400 text-white/70'">
                    <span>{{ disliked ? '👎' : '👎🏻' }}</span>
                    <span>{{ dislikes }}</span>
                </button>
            </div>

            <!-- Quiz Button -->
            <div class="text-center">
                <button @click="goToQuiz"
                    class="px-6 py-2 bg-accent hover:bg-accent-light text-black font-semibold rounded-full transition shadow-md">
                    📚 Take Comic Quiz
                </button>
            </div>
        </div>

        <div v-else class="text-center text-red-300 text-lg font-semibold mt-20">
            ⚠️ Sorry! The comic couldn't be loaded.
        </div>
    </section>

    <ChatBot class="fixed bottom-4 right-4" />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VuePdfApp from 'vue3-pdf-app'
import 'vue3-pdf-app/dist/icons/main.css'
import ChatBot from '@/components/ComicBot.vue'

const route = useRoute()
const router = useRouter()

const comic = ref(null)
const src = ref(null)
const likes = ref(0)
const dislikes = ref(0)
const liked = ref(false)
const disliked = ref(false)

async function loadComicData() {
    try {
        const token = JSON.parse(localStorage.getItem('user'))?.token
        const res = await fetch(`/api/v1/safety/comic/${route.params.id}`, {
            headers: { Authorization: `Bearer ${token}` }
        })

        const data = await res.json()
        if (data.success && data.data?.comic) {
            comic.value = data.data.comic
            likes.value = comic.value.likes || 0
            dislikes.value = comic.value.dislikes || 0
            liked.value = comic.value.userLiked || false
            disliked.value = comic.value.userDisliked || false
            src.value = comic.value.pdfUrl
        }
    } catch (error) {
        console.error('⚠ Failed to load comic:', error)
    }
}

async function refreshReaction() {
    const token = JSON.parse(localStorage.getItem('user'))?.token
    try {
        const res = await fetch(`/api/v1/safety/comic/${route.params.id}/reaction`, {
            headers: { Authorization: `Bearer ${token}` }
        })
        const data = await res.json()
        if (data.success && data.data) {
            liked.value = data.data.liked
            disliked.value = data.data.disliked
        }
    } catch (error) {
        console.warn('⚠ Failed to refresh reaction:', error)
    }
}

async function toggleLike() {
    const token = JSON.parse(localStorage.getItem('user'))?.token
    try {
        await fetch(`/api/v1/safety/comic/${route.params.id}/like`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
        })
        await loadComicData()
        await refreshReaction()
    } catch (e) {
        console.error('Like failed:', e)
    }
}

async function toggleDislike() {
    const token = JSON.parse(localStorage.getItem('user'))?.token
    try {
        await fetch(`/api/v1/safety/comic/${route.params.id}/dislike`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` }
        })
        await loadComicData()
        await refreshReaction()
    } catch (e) {
        console.error('Dislike failed:', e)
    }
}

function goToQuiz() {
    router.push({ name: 'safetycomicquiz', params: { id: route.params.id } })
}

onMounted(() => {
    loadComicData()
    // also track the view
    const token = JSON.parse(localStorage.getItem('user'))?.token
    fetch(`/api/v1/safety/comic/${route.params.id}/view`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
    }).catch(() => { })
})
</script>

<style scoped>
.glass-card {
    @apply bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl p-4 shadow-lg;
}

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
    animation: fade-in 0.7s ease-out both;
}
</style>
