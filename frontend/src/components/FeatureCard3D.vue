<template>
  <div
    class="feature-card-3d bg-white/10 backdrop-blur-md border border-primary-light rounded-2xl p-4 shadow-xl transition-transform transform duration-300 hover:scale-105 hover:shadow-card-hover">
    <div class="flex flex-col items-center h-full">
      <img :src="img" class="w-16 h-16 object-contain mb-3 drop-shadow-lg" :alt="`${title} Icon`" />
      <h3 class="text-lg font-bold text-accent text-center mb-1">
        {{ title }}
      </h3>
      <p class="text-sm text-neutral-light text-center leading-relaxed">
        {{ desc }}
      </p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  img: String,
  desc: String,
})
</script>

<style scoped>
.feature-card-3d {
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}
</style>
