<template>
    <div class="w-full bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-6 shadow-xl">
        <h2 class="text-xl font-bold text-accent mb-4 text-center">📊 Skill Usage Chart</h2>
        <Bar v-if="chartData" :data="chartData" :options="chartOptions" />
        <p v-else class="text-white text-center">Loading chart data...</p>
    </div>
</template>

<script setup>
import { Bar } from 'vue-chartjs'
import {
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    BarElement,
    CategoryScale,
    LinearScale
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const props = defineProps({
    usageData: {
        type: Array,
        required: true,
        default: () => [],
    },
})

// Prepare chart data
const skillColors = [
    '#4DD0E1', // Sky Blue
    '#FF80AB', // Pink
    '#FFD93D', // Yellow
    '#5C6BC0', // Violet
    '#90CAF9'  // Soft Blue
]

const chartData = {
    labels: props.usageData.map(item => item.title),
    datasets: [
        {
            label: 'Usage Time (minutes)',
            data: props.usageData.map(item => item.usage || 0),
            backgroundColor: skillColors,
            borderRadius: 6,
        },
    ],
}

const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
        y: {
            beginAtZero: true,
            ticks: { color: '#CFD8DC' },
            grid: { color: 'rgba(255, 255, 255, 0.1)' }
        },
        x: {
            ticks: { color: '#CFD8DC' },
            grid: { display: false }
        }
    },
    plugins: {
        legend: {
            labels: { color: '#CFD8DC' }
        },
        tooltip: {
            backgroundColor: '#263238',
            titleColor: '#FFD93D',
            bodyColor: '#FFFFFF',
        }
    }
}
</script>

<style scoped>
div {
    min-height: 320px;
}
</style>
  
