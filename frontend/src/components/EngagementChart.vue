<template>
    <div class="bg-background-paper p-4 rounded-xl shadow-card">
        <h3 class="text-lg font-bold mb-2">{{ title }}</h3>
        <canvas ref="chartCanvas"></canvas>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
    data: Object,
    title: String
});

const chartCanvas = ref();

onMounted(() => {
    new Chart(chartCanvas.value, {
        type: 'bar',
        data: {
            labels: props.data.labels,
            datasets: [{
                label: props.title,
                data: props.data.values,
                backgroundColor: '#BD93F9'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false }
            }
        }
    });
});
</script>
  
