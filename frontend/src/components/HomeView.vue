<template>
  <div class="max-w-6xl mx-auto mt-16 px-4 text-text-base animate-fade-in">
    <!-- Header Banner -->
    <section
      class="max-w-3xl mx-auto bg-white/10 backdrop-blur-md border border-primary-light rounded-2xl px-6 py-5 shadow-xl text-center">
      <h1 class="text-3xl md:text-4xl font-extrabold text-muted tracking-tight leading-tight">
        ✨ Choose a Life Skill to Learn Today!
      </h1>
    </section>

    <!-- CTA Buttons -->
    <div class="mt-8 flex flex-col items-center gap-4 animate-scale-up">
      <router-link to="/join-us"
        class="bg-primary hover:bg-primary-light text-white font-semibold py-3 px-6 rounded-full transition-all duration-300 shadow-lg">
        🚀 Join Us Now!
      </router-link>
      <router-link to="/login" class="text-sm text-secondary-light hover:underline">
        👋 Already a Pupil? <strong>Log In!</strong>
      </router-link>
    </div>

    <!-- 3D Skill Card Carousel -->
    <section class="relative w-full h-96 mt-20 mb-32">
      <div class="slider" style="--quantity: 6">
        <div class="item" style="--position: 1">
          <FeatureCard3D title="🚨 Emergency Skills" img="https://cdn-icons-png.flaticon.com/128/3900/3900771.png"
            desc="Learn safety skills and become an Emergency Expert!" />
        </div>
        <div class="item" style="--position: 2">
          <FeatureCard3D title="💰 Money Smart" img="https://cdn-icons-png.flaticon.com/128/3135/3135706.png"
            desc="Track your coins, save smart, and plan like a pro!" />
        </div>
        <div class="item" style="--position: 3">
          <FeatureCard3D title="📓 Emotional Diary" img="https://cdn-icons-png.flaticon.com/512/2232/2232688.png"
            desc="Write, reflect, and grow with AI-powered journaling." />
        </div>
        <div class="item" style="--position: 4">
          <FeatureCard3D title="🗣 Speak Confidently" img="https://cdn-icons-png.flaticon.com/512/4333/4333609.png"
            desc="Use AI to improve your English speaking skills!" />
        </div>
        <div class="item" style="--position: 5">
          <FeatureCard3D title="🛡️ Basic Manners" img="https://cdn-icons-png.flaticon.com/128/4796/4796282.png"
            desc="Learn how to be kind, clean, and confident!" />
        </div>
        <div class="item" style="--position: 6">
          <FeatureCard3D title="🏆 Earn Badges" img="https://cdn-icons-png.flaticon.com/512/7641/7641727.png"
            desc="Complete fun activities to earn your badge collection!" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import FeatureCard3D from '@/components/FeatureCard3D.vue'
</script>

<style scoped>
.slider {
  position: absolute;
  width: 200px;
  height: 260px;
  top: 60%;
  left: 50%;
  transform-style: preserve-3d;
  transform: perspective(800px) translateX(-50%) translateY(-50%) rotateX(-10deg);
  animation: autoRun 28s linear infinite;
  z-index: 1;
}

@keyframes autoRun {
  from {
    transform: perspective(800px) translateX(-50%) translateY(-50%) rotateX(-10deg) rotateY(0deg);
  }

  to {
    transform: perspective(800px) translateX(-50%) translateY(-50%) rotateX(-10deg) rotateY(360deg);
  }
}

.slider .item {
  position: absolute;
  inset: 0;
  transform: rotateY(calc((var(--position) - 1) * (360 / var(--quantity)) * 1deg)) translateZ(300px);
  transition: all 0.4s ease;
}

@media screen and (max-width: 1023px) {
  .slider {
    width: 160px;
    height: 220px;
  }

  .slider .item {
    transform: rotateY(calc((var(--position) - 1) * (360 / var(--quantity)) * 1deg)) translateZ(250px);
  }
}

@media screen and (max-width: 767px) {
  .slider {
    width: 120px;
    height: 180px;
  }

  .slider .item {
    transform: rotateY(calc((var(--position) - 1) * (360 / var(--quantity)) * 1deg)) translateZ(180px);
  }
}
</style>
