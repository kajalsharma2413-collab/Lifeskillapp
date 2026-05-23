<template>
    <!-- Back Button -->
    <router-link to="/financevideo"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>

    <section class="max-w-4xl mx-auto p-6 text-white">
        <div v-if="video" class="animate-fade-in">
            <h2 class="text-3xl font-extrabold text-accent mb-4">
                💰 {{ video.title }}
            </h2>

            <!-- Video -->
            <div class="w-full mb-6 rounded-xl overflow-hidden shadow-xl aspect-video bg-black">
                <iframe v-if="video.videoUrl" :src="embedUrl(video.videoUrl)" frameborder="0"
                    class="w-full h-full rounded-xl"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen></iframe>
            </div>

            <p class="text-lg text-neutral-light text-center mb-6">
                {{ video.description }}
            </p>

            <!-- Badge -->
            <div v-if="video.badge_id" class="flex justify-center items-center gap-3 mb-6">
                <img :src="video.badge_url" alt="badge" class="w-10 h-10" />
                <span class="font-semibold">
                    🏆 {{ video.badge_name }} (+{{ video.badge_points }} pts)
                </span>
            </div>

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
                    🧠 Take Quiz
                </button>
            </div>
        </div>

        <div v-else class="text-center text-red-300 text-lg font-semibold mt-20">
            ⚠️ Sorry! The video couldn't be loaded.
        </div>
    </section>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const video = ref(null);
const likes = ref(0);
const dislikes = ref(0);
const liked = ref(false);
const disliked = ref(false);

function embedUrl(url) {
    // convert normal YouTube link into embeddable
    if (url.includes("youtu.be")) {
        const id = url.split("youtu.be/")[1].split("?")[0];
        return `https://www.youtube.com/embed/${id}`;
    }
    return url;
}

onMounted(async () => {
    try {
        const token =localStorage.getItem("firebase_token");

        // Get video
        const res = await fetch(`/api/v1/finance/video/${route.params.id}`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();

        if (data.success && data.data?.video) {
            video.value = data.data.video;
            likes.value = video.value.likes || 0;
            dislikes.value = video.value.dislikes || 0;

            // Track view
            await fetch(`/api/v1/finance/video/${route.params.id}/view`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
            });

            // ✅ Fetch reaction status
            const reactionRes = await fetch(
                `/api/v1/finance/video/${route.params.id}/reaction`,
                {
                    headers: { Authorization: `Bearer ${token}` },
                }
            );
            const reactionData = await reactionRes.json();
            if (reactionData.success && reactionData.data) {
                liked.value = reactionData.data.liked || false;
                disliked.value = reactionData.data.disliked || false;
            }
        }
    } catch (error) {
        console.error("Error fetching video data:", error);
    }
});

async function toggleLike() {
    const token = localStorage.getItem("firebase_token");
    if (!video.value) return;

    if (liked.value) {
        likes.value--;
        liked.value = false;
        await fetch(`/api/v1/finance/video/${video.value.id}/remove-like`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
    } else {
        likes.value++;
        liked.value = true;
        await fetch(`/api/v1/finance/video/${video.value.id}/like`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
        if (disliked.value) {
            dislikes.value--;
            disliked.value = false;
        }
    }
}

async function toggleDislike() {
    const token = localStorage.getItem("firebase_token");
    if (!video.value) return;

    if (disliked.value) {
        dislikes.value--;
        disliked.value = false;
        await fetch(`/api/v1/finance/video/${video.value.id}/remove-dislike`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
    } else {
        dislikes.value++;
        disliked.value = true;
        await fetch(`/api/v1/finance/video/${video.value.id}/dislike`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
        });
        if (liked.value) {
            likes.value--;
            liked.value = false;
        }
    }
}

function goToQuiz() {
    router.push({ name: "financevideoquiz", params: { id: route.params.id } });
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
