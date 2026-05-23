<template>
    <div class="bg-background-paper p-4 rounded-xl shadow-card text-center">
        <div class="text-4xl mb-2">{{ icon }}</div>
        <div class="text-lg font-semibold">{{ title }}</div>
        <div class="text-2xl font-bold text-primary">{{ value }}</div>
    </div>
</template>

<script setup>
defineProps({
    title: String,
    value: [Number, String],
    icon: String
});
</script>
  
