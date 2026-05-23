<template>
    <div class="relative w-full h-60 rounded-2xl overflow-hidden shadow-card hover:shadow-elevated transform transition-transform duration-300 cursor-pointer group"
        @mouseenter="isHovered = true" @mouseleave="isHovered = false" @click="handleClick">
        <!-- Image -->
        <div class="w-full h-full">
            <img :src="image" :alt="title"
                class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                :class="{ 'brightness-50 blur-sm': isComingSoon && isHovered }" />
        </div>

        <!-- Info on Hover -->
        <transition name="slide-fade">
            <div v-if="isHovered"
                class="absolute bottom-0 left-0 right-0 bg-neutral-dark/90 backdrop-blur-lg p-4 text-center text-white">
                <h3 class="text-lg font-bold tracking-wide uppercase text-accent">
                    {{ isComingSoon ? 'COMING SOON : Basic Manners' : title }}
                </h3>
                <p class="text-sm text-neutral-light mt-1 leading-snug">
                    {{ isComingSoon ? 'This Basic Manners skill will be available soon. Stay tuned!' : description }}
                </p>
            </div>
        </transition>
    </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
    image: String,
    title: String,
    description: String,
    isComingSoon: Boolean,
    route: String
})

const router = useRouter()
const isHovered = ref(false)

const handleClick = () => {
    if (props.route && !props.isComingSoon) {
        router.push(props.route)
    }
}
</script>

<style scoped>
.slide-fade-enter-active {
    transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
    transition: all 0.3s ease-in;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
    transform: translateY(100%);
    opacity: 0;
}
</style>
  
