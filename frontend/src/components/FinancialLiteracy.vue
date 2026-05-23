<template>
    <!-- Back Button -->
    <router-link to="/lifeskills"
        class="glass-card mb-6 p-6 inline-flex items-center gap-2 hover:bg-accent-light text-xl text-accent font-semibold px-4 py-2 rounded-full shadow transition mb-6">
        <span>⬅️ Back</span>
    </router-link>
    <section class="p-8 max-w-6xl mx-auto text-white">
        <!-- Title -->
        <h1 class="text-4xl font-bold text-accent mb-3 animate-fade-in">💰 Finance Skills</h1>
        <p class="text-lg text-text-muted mb-8 animate-fade-in">
            Understand money management to make smart financial decisions! Learn budgeting, saving, and spending wisely.
        </p>

        <!-- Watch Animation Card -->
        <div ref="videoCardRef" :style="videoCardStyle"
            class="glass-card mb-10 md:flex md:items-center gap-6 transition-shadow duration-300 hover:shadow-elevated">
            <img src="@/assets/finance.png" alt="Watch Finance Animation"
                class="w-full md:w-1/2 rounded-xl shadow-md object-cover max-h-64" />
            <div class="p-4 md:w-1/2">
                <h2 class="text-2xl font-bold text-accent mb-2">🎬 Watch Animation</h2>
                <p class="text-sm text-white/80 mb-4">
                    Learn about saving and spending through an engaging story.
                </p>
                <router-link to="/financevideo"
                    class="inline-block bg-accent hover:bg-accent-light text-black font-semibold px-5 py-2 rounded-full transition">
                    ▶️ Watch Now
                </router-link>
            </div>
        </div>

        <!-- Play Game Card -->
        <div ref="gameCardRef" :style="gameCardStyle"
            class="glass-card md:flex md:flex-row-reverse md:items-center gap-6 transition-shadow duration-300 hover:shadow-elevated">
            <img src="@/assets/finance-game.jpg" alt="Play Budget Game"
                class="w-full md:w-1/2 rounded-xl shadow-md object-cover max-h-64" />
            <div class="p-4 md:w-1/2">
                <h2 class="text-2xl font-bold text-accent mb-2">🕹️ Play Budgeting Game</h2>
                <p class="text-sm text-white/80 mb-4">
                    Test your money management skills in a fun interactive game!
                </p>
                <router-link to="/financegame"
                    class="inline-block bg-accent hover:bg-accent-light text-black font-semibold px-5 py-2 rounded-full transition">
                    🎮 Play Now
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
const gameCardRef = ref(null)

// Parallax effect
const { tilt: tiltV, roll: rollV } = useParallax(videoCardRef)
const { tilt: tiltG, roll: rollG } = useParallax(gameCardRef)

const videoCardStyle = computed(() => ({
    transform: `perspective(1000px) rotateX(${tiltV.value * 5}deg) rotateY(${rollV.value * 5}deg)`,
    transition: 'transform 0.2s ease-out',
    willChange: 'transform',
}))

const gameCardStyle = computed(() => ({
    transform: `perspective(1000px) rotateX(${tiltG.value * 5}deg) rotateY(${rollG.value * 5}deg)`,
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
  
