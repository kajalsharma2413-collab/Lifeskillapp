<template>
    <div class="bg-background-paper p-4 rounded-xl shadow-card">
        <h3 class="text-lg font-bold mb-2">{{ title }}</h3>
        <canvas ref="lineChart"></canvas>
    </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import Chart from 'chart.js/auto';

const props = defineProps({
    data: Object,
    title: String
});

const lineChart = ref();

onMounted(() => {
    new Chart(lineChart.value, {
        type: 'line',
        data: {
            labels: props.data.labels,
            datasets: [{
                label: props.title,
                data: props.data.values,
                borderColor: '#8BE9FD',
                backgroundColor: 'rgba(139, 233, 253, 0.2)',
                tension: 0.3
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
  
