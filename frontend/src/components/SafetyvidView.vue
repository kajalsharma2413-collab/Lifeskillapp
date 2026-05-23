<template>
    <!-- Back Button -->
    <router-link to="/safetyvideo"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>
    <section class="max-w-4xl mx-auto p-6 text-white">
        <div v-if="video" class="animate-fade-in">
            <h2 class="text-3xl font-extrabold text-accent mb-4">🎥 {{ video.title }}</h2>

            <!-- Video -->
            <div class="w-full mb-6 rounded-xl overflow-hidden shadow-xl aspect-video bg-black">
                <!-- YouTube Embed -->
                <template v-if="isYouTube(video.videoUrl)">
                    <iframe :src="`https://www.youtube.com/embed/${extractYouTubeId(video.videoUrl)}`" frameborder="0"
                        class="w-full h-full rounded-xl"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen></iframe>
                </template>

                <!-- Direct Video -->
                <template v-else>
                    <video controls :src="video.videoUrl" class="w-full h-full object-contain rounded-xl"></video>
                </template>
            </div>

            <p class="text-lg text-neutral-light text-center mb-6">{{ video.description }}</p>

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

            <div class="text-center">
                <button @click="goToQuiz"
                    class="px-6 py-2 bg-accent hover:bg-accent-light text-black font-semibold rounded-full transition shadow-md">
                    📝 Take Quiz
                </button>
            </div>
        </div>

        <div v-else class="text-center text-red-300 text-lg font-semibold mt-20">
            ⚠️ Sorry! The video couldn't be loaded.
        </div>
    </section>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const video = ref(null)
const likes = ref(0)
const dislikes = ref(0)
const liked = ref(false)
const disliked = ref(false)

onMounted(async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch(`/api/v1/safety/video/${route.params.id}`, {
            headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        console.log('Video data:', data)

        if (data.success && data.data?.video) {
            video.value = data.data.video
            likes.value = data.data.video.likes || 0
            dislikes.value = data.data.video.dislikes || 0
            liked.value = data.data.video.userLiked || false
            disliked.value = data.data.video.userDisliked || false
        } else {
            throw new Error('Video not found')
        }
    } catch (e) {
        console.error('❌ Failed to load video', e)
    }
})

// ✅ Check if the link is a YouTube link
function isYouTube(url) {
    return /youtu\.be|youtube\.com/.test(url || '')
}

// ✅ Extract YouTube Video ID
function extractYouTubeId(url) {
    const regExp = /(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{11})/
    const match = url.match(regExp)
    return match ? match[1] : ''
}

// ✅ Like Toggle Logic
async function toggleLike() {
    if (liked.value) {
        likes.value--
        liked.value = false
        await postReaction('remove-like')
    } else {
        likes.value++
        liked.value = true
        await postReaction('like')
        if (disliked.value) {
            dislikes.value--
            disliked.value = false
        }
    }
}

// ✅ Dislike Toggle Logic
async function toggleDislike() {
    if (disliked.value) {
        dislikes.value--
        disliked.value = false
        await postReaction('remove-dislike')
    } else {
        dislikes.value++
        disliked.value = true
        await postReaction('dislike')
        if (liked.value) {
            likes.value--
            liked.value = false
        }
    }
}

// ✅ Backend reaction update
async function postReaction(action) {
    const token = localStorage.getItem('firebase_token')
    try {
        await fetch(`/api/v1/safety/video/${route.params.id}/${action}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${token}` },
        })
    } catch (e) {
        console.warn('⚠ Reaction not saved to backend', e)
    }
}

function goToQuiz() {
    router.push({ name: 'safetyvideoquiz', params: { id: route.params.id } })
}
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

.aspect-video {
    aspect-ratio: 16 / 9;
}
</style>
