<template>
    <div class="flex min-h-screen text-white">
        <!-- Admin Sidebar -->
        <div class="w-64 min-h-screen bg-background-paper shadow-elevated p-4">
            <h2 class="text-2xl font-bold text-primary mb-6">Admin</h2>
            <nav class="space-y-4">
                <RouterLink to="/admin-dashboard" class="flex items-center space-x-2 text-text-base hover:text-primary">
                    <span>📊</span><span>Dashboard</span>
                </RouterLink>
                <RouterLink to="/admin-skill" class="flex items-center space-x-2 text-text-base hover:text-primary">
                    <span>📚</span><span>LifeSkill</span>
                </RouterLink>
                <RouterLink to="/admin-safety" class="flex items-center space-x-2 text-text-base hover:text-primary">
                    <span>🦺</span><span>Safety Skill</span>
                </RouterLink>
                <RouterLink to="/admin-finance" class="flex items-center space-x-2 text-text-base hover:text-primary">
                    <span>💰</span><span>Finance Skill</span>
                </RouterLink>
                <RouterLink to="/admin-dashboard" class="flex items-center space-x-2 text-text-base hover:text-primary">
                    <span>🧒</span><span>Basic Manner : Coming Soon</span>
                </RouterLink>
                <RouterLink to="/admin-badge" class="flex items-center space-x-2 text-text-base hover:text-primary">
      <span>🏅</span><span>Badges</span>
    </RouterLink>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="flex-1 overflow-y-auto px-4 py-6">
            <section class="max-w-7xl mx-auto">
                <!-- Header -->
                <div class="text-center mb-10">
                    <h1 class="text-4xl font-extrabold text-red-400 animate-fade-in">
                        🛠 Admin Skill Manager
                    </h1>
                    <p class="text-lg text-text-muted mt-2 animate-fade-in">
                        Manage content for each essential life skill below.
                    </p>
                </div>

                <!-- Skill Cards -->
                <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    <div v-for="(skill, index) in skills" :key="skill.title"
                        class="relative group cursor-pointer transition-all"
                        @click="skill.route && navigateToSkill(skill.route)"
                        @mouseover="hoverIndex = skill.title === 'Coming Soon: Basic Manners' ? index : null"
                        @mouseleave="hoverIndex = null">
                        <div
                            class="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-all duration-300 hover:animate-fade-in text-black">
                            <img :src="skill.title === 'Coming Soon: Basic Manners' && hoverIndex === index ? comingsoon : skill.image"
                                alt="" class="w-16 h-16 mx-auto mb-4" />
                            <h3 class="text-lg font-bold text-center">{{ skill.title }}</h3>
                            <p class="text-sm text-center text-gray-600 mt-2">{{ skill.description }}</p>
                        </div>

                        <!-- "Coming Soon" Badge -->
                        <div v-if="skill.title === 'Coming Soon: Basic Manners' && hoverIndex === index"
                            class="absolute top-2 right-2 bg-yellow-400 text-black font-bold text-xs px-2 py-1 rounded">
                            Coming Soon
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import safetyImg from '@/assets/safety.png'
import financeImg from '@/assets/finance.png'
import problemImg from '@/assets/problem.png'
import mannersImg from '@/assets/manners.png'
import comingsoon from '@/assets/coming-soon.jpg'

const router = useRouter()
const hoverIndex = ref(null)

const skills = [
    {
        title: 'Safety Skills',
        image: safetyImg,
        description: 'Manage emergency-related content and quizzes.',
        route: '/admin-safety',
    },
    {
        title: 'Financial Literacy',
        image: financeImg,
        description: 'Add or update finance videos and levels.',
        route: '/admin-finance',
    },
    
    {
        title: 'Coming Soon: Basic Manners',
        image: mannersImg,
        description: 'Kindness, empathy, hygiene and respectful behavior.',
        route: null,
    },
]
function navigateToSkill(route) {
    router.push(route)
}
</script>

<style scoped>
@keyframes fade-in {
    0% {
        opacity: 0;
        transform: scale(0.95);
    }

    100% {
        opacity: 1;
        transform: scale(1);
    }
}

.animate-fade-in {
    animation: fade-in 0.6s ease-out both;
}
</style>
