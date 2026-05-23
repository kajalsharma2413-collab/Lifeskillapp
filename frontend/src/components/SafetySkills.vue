<template>
    <!-- Back Button -->
    <router-link to="/lifeskills"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>
    <section class="p-8 max-w-6xl mx-auto text-white">
        <!-- Title -->
        <h1 class="text-4xl font-bold text-accent mb-3 animate-fade-in">🛡️ Safety Skills</h1>
        <p class="text-lg text-text-muted mb-8 animate-fade-in">
            Learn essential safety skills to stay safe and prepared in any situation. This module covers how to react in
            emergencies like fire, first aid, and natural disasters.
        </p>

        <!-- Watch Video Card -->
        <div ref="videoCardRef" :style="videoCardStyle"
            class="glass-card mb-10 md:flex md:items-center gap-6 transition-shadow duration-300 hover:shadow-elevated">
            <img src="@/assets/safety-video.png" alt="Watch Safety Video"
                class="w-full md:w-1/2 rounded-xl shadow-md object-cover" />
            <div class="p-4 md:w-1/2">
                <h2 class="text-2xl font-bold text-accent mb-2">🎥 Watch Safety Video</h2>
                <p class="text-sm text-white/80 mb-4">
                    Understand safety practices through an engaging and informative video.
                </p>
                <router-link to="/safetyvideo"
                    class="inline-block bg-accent hover:bg-accent-light text-black font-semibold px-5 py-2 rounded-full transition">
                    ▶️ Watch Now
                </router-link>
            </div>
        </div>

        <!-- Read Comic Card -->
        <div ref="comicCardRef" :style="comicCardStyle"
            class="glass-card md:flex md:flex-row-reverse md:items-center gap-6 transition-shadow duration-300 hover:shadow-elevated">
            <img src="@/assets/safety-comic.png" alt="Read Safety Comic"
                class="w-full md:w-1/2 rounded-xl shadow-md object-cover" />
            <div class="p-4 md:w-1/2">
                <h2 class="text-2xl font-bold text-accent mb-2">📚 Read Safety Comic</h2>
                <p class="text-sm text-white/80 mb-4">
                    Explore safety tips through a fun, illustrated comic experience.
                </p>
                <router-link to="/safetycomic"
                    class="inline-block bg-accent hover:bg-accent-light text-black font-semibold px-5 py-2 rounded-full transition">
                    📖 Read Now
                </router-link>
            </div>
        </div>
    </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useParallax } from '@vueuse/core'

// Refs for cards
const videoCardRef = ref(null)
const comicCardRef = ref(null)

// Parallax effects
const { tilt: tiltV, roll: rollV } = useParallax(videoCardRef)
const { tilt: tiltC, roll: rollC } = useParallax(comicCardRef)

const videoCardStyle = computed(() => ({
    transform: `perspective(1000px) rotateX(${tiltV.value * 5}deg) rotateY(${rollV.value * 5}deg)`,
    transition: 'transform 0.2s ease-out',
    willChange: 'transform',
}))

const comicCardStyle = computed(() => ({
    transform: `perspective(1000px) rotateX(${tiltC.value * 5}deg) rotateY(${rollC.value * 5}deg)`,
    transition: 'transform 0.2s ease-out',
    willChange: 'transform',
}))
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

.animate-fade-in {
    animation: fade-in 0.8s ease-out both;
}
</style>
  
