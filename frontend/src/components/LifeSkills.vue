<template>
    <div class="flex min-h-screen text-white">
        <!-- Sidebar -->
        <Sidebar />

        <!-- Main Content -->
        <div class="flex-1 overflow-y-auto px-4 py-6">
            <section class="max-w-7xl mx-auto">
                <!-- Header -->
                <div class="text-center mb-10">
                    <h1 class="text-4xl font-extrabold text-accent animate-fade-in">
                        💡 Life Skills
                    </h1>
                    <p class="text-lg text-text-muted mt-2 animate-fade-in">
                        Explore essential life skills to help you grow and succeed.
                    </p>
                </div>

                <!-- Skill Cards -->
                <div v-if="skills.length" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                    <div v-for="(skill, index) in skills" :key="skill.title"
                        class="relative group cursor-pointer transition-all"
                        @mouseover="hoverIndex = skill.title === 'Coming Soon: Basic Manners' ? index : null"
                        @mouseleave="hoverIndex = null" @click="trackView(skill)">
                        <SkillCard
                            :image="skill.title === 'Coming Soon: Basic Manners' && hoverIndex === index ? comingsoon : resolveImage(skill.image)"
                            :title="skill.title" :description="skill.description" :route="skill.route"
                            :is-coming-soon="skill.title === 'Coming Soon: Basic Manners'" />
                        <!-- Optional: Overlay "Coming Soon" Label -->
                        <div v-if="skill.title === 'Coming Soon: Basic Manners' && hoverIndex === index"
                            class="absolute top-2 right-2 bg-yellow-400 text-black font-bold text-xs px-2 py-1 rounded">
                            Coming Soon
                        </div>
                    </div>
                </div>

                <!-- Loader -->
                <div v-else class="text-center text-white/70 mt-10">
                    ⏳ Loading life skills...
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Sidebar from '@/components/SideBar.vue'
import SkillCard from '@/components/SkillCard.vue'

import safetyImg from '@/assets/safety.png'
import financeImg from '@/assets/finance.png'
import communicationImg from '@/assets/communication.png'
import problemImg from '@/assets/problem.png'
import mannersImg from '@/assets/manners.png'
import comingsoon from '@/assets/coming-soon.jpg'

const hoverIndex = ref(null)
const skills = ref([])
const token = localStorage.getItem('firebase_token')

// Map backend image keys to local assets
const imageMap = {
    safety_img: safetyImg,
    finance_img: financeImg,
    communication_img: communicationImg,
    problem_img: problemImg,
    manners_img: mannersImg,
}
const resolveImage = (imgKey) => imageMap[imgKey] || comingsoon

// Fetch life skills from backend
const fetchSkills = async () => {
    try {
        const res = await fetch('/api/v1/skills')
        const data = await res.json()
        if (res.ok && data.success) {
            skills.value = data.data
        } else {
            console.error('⚠️ Failed to load skills', data)
        }
    } catch (err) {
        console.error('❌ Error fetching skills:', err)
    }
}

// Track skill view
const trackView = async (skill) => {
    try {
        if (!skill.route) return // skip coming soon

        let endpoint = null
        if (skill.title.includes('Safety')) endpoint = '/api/v1/skills/safety/view'
        else if (skill.title.includes('Finance')) endpoint = '/api/v1/skills/finance/view'
        else if (skill.title.includes('Communication')) endpoint = '/api/v1/skills/communication/view'
        else if (skill.title.includes('Problem')) endpoint = '/api/v1/skills/problem-solving/view'

        if (endpoint) {
            const token = localStorage.getItem('firebase_token')
            await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`
                }
            })
            console.log(`✅ Tracked view for ${skill.title}`)
        }
    } catch (err) {
        console.error('❌ Failed to track skill view:', err)
    }
}

onMounted(() => {
    fetchSkills()
})
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

.animate-fade-in {
    animation: fade-in 0.7s ease-out both;
}
</style>
