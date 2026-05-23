<template>
  <div class="min-h-screen bg-background-soft text-text-base bg-no-repeat bg-cover bg-center"
    style="background-image: url('/path/to/your/background-image.png')">
    <div class="flex">
      <!-- Sidebar -->
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
      <div class="flex-1 p-6 space-y-6 bg-background-soft/90 rounded-xl backdrop-blur-md">
        <h1 class="text-3xl font-bold mb-4">Admin Dashboard</h1>

        <!-- Summary Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <SummaryCard title="Total Users" :value="summary.total_users" icon="👥" />
          <SummaryCard title="Active (7d)" :value="summary.active_users" icon="✅" />
          <SummaryCard title="Quiz Attempts" :value="summary.quiz_attempts" icon="📝" />
          <SummaryCard title="Badges Earned" :value="summary.badges_earned" icon="🏅" />
        </div>

        <!-- Engagement Charts -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <EngagementChart v-if="skillEngagement.labels.length" :data="skillEngagement" title="Skill Engagement" />
          <MoodTrendsChart v-if="moodTrends.labels.length" :data="moodTrends" title="Mood Trends (7 days)" />
        </div>

        <!-- Alerts -->
        <div>
          <div class="flex justify-between items-center mb-4">
            <h2 class="text-xl font-semibold">Alerts & Flags</h2>
            <button class="bg-accent text-white px-4 py-2 rounded-lg hover:bg-accent-dark transition"
              @click="openAddAlertModal">+ Add Alerts</button>
          </div>
          <ul class="space-y-4">
            <li v-for="(alert, index) in alerts" :key="index"
              class="bg-warning-dark text-warning-light p-4 rounded-xl shadow-card flex justify-between items-start">
              <div>
                <p class="text-lg font-bold">{{ alert.type.toUpperCase() }}</p>
                <p class="text-base mt-1">{{ alert.message }}</p>
                <p class="text-sm text-warning-light/90 mt-2">Suggested: {{ alert.suggested_action }}</p>
              </div>
              <div class="space-x-2">
                <button @click="editAlert(index)"
                  class="bg-accent-dark text-white px-3 py-1 rounded-xl hover:bg-accent">
                  Edit
                </button>
                <button @click="deleteAlert(index)"
                  class="bg-danger-dark text-white px-3 py-1 rounded-xl hover:bg-danger">
                  Delete
                </button>
              </div>
            </li>
          </ul>
          <!-- Add Alert Modal -->
          <div v-if="showAddAlertModal"
            class="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
            <div class="bg-white rounded-lg p-6 w-96 shadow-lg">
              <h3 class="text-lg font-semibold mb-4">Add New Alert</h3>

              <input v-model="newAlert.type" type="text" placeholder="Type (e.g. warning, error)"
                class="w-full border rounded p-2 mb-2" />

              <textarea v-model="newAlert.message" placeholder="Message"
                class="w-full border rounded p-2 mb-2"></textarea>

              <input v-model="newAlert.suggested_action" type="text" placeholder="Suggested Action"
                class="w-full border rounded p-2 mb-4" />

              <div class="flex justify-end space-x-2">
                <button @click="closeAddAlertModal" class="px-4 py-2 rounded border text-black">
                  Cancel
                </button>
                <button @click="submitNewAlert" class="px-4 py-2 rounded bg-accent text-white">
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { RouterLink } from "vue-router";
import SummaryCard from "@/components/SummaryCard.vue";
import EngagementChart from "@/components/EngagementChart.vue";
import MoodTrendsChart from "@/components/MoodTrendsChart.vue";

// Dashboard states
const summary = reactive({
  total_users: 0,
  active_users: 0,
  quiz_attempts: 0,
  badges_earned: 0,
});

const skillEngagement = reactive({
  labels: [],
  values: [],
});

const moodTrends = reactive({
  labels: [],
  values: [],
});

// Alerts & Flags
const alerts = ref([]);
const flags = ref([]);

// Token
const token = localStorage.getItem("firebase_token");

// Fetch Dashboard Stats
async function fetchStats() {
  try {
    const res = await fetch("/api/v1/admin/dashboard/stats", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      summary.total_users = data.data.total_users || 0;
      summary.active_users = data.data.active_users || 0;
      summary.quiz_attempts = data.data.quiz_attempts || 0;
      summary.badges_earned = data.data.badges_earned || 0;
    }
  } catch (err) {
    console.error("❌ Failed to fetch dashboard stats", err);
  }
}

// Fetch Skill Engagement
async function fetchSkillEngagement() {
  try {
    const res = await fetch("/api/v1/admin/dashboard/skill-engagement", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      skillEngagement.labels = data.data.map((d) => d.skill);
      skillEngagement.values = data.data.map((d) => d.engagement);
    }
  } catch (err) {
    console.error("❌ Failed to fetch skill engagement", err);
  }
}

// Fetch Mood Trends
async function fetchMoodTrends() {
  try {
    const res = await fetch("/api/v1/admin/dashboard/mood-trends?days=7", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      moodTrends.labels = data.data.map((d) => d.date);
      moodTrends.values = data.data.map((d) => d.average_mood);
    }
  } catch (err) {
    console.error("❌ Failed to fetch mood trends", err);
  }
}

// ----------------------
// Alerts API
// ----------------------
async function fetchAlerts() {
  const res = await fetch("/api/v1/admin/dashboard/alerts", {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (data.success) alerts.value = data.data;
}

async function resolveAlert(alertId) {
  await fetch(`/api/v1/admin/dashboard/alerts/${alertId}/resolve`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
  fetchAlerts();
}

async function deleteAlert(alertId) {
  await fetch(`/api/v1/admin/dashboard/alerts/${alertId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  fetchAlerts();
}

// ----------------------
// Content Flags API
// ----------------------
async function fetchFlags(status = null, priority = null, limit = 50) {
  try {
    let url = `/api/v1/admin/dashboard/flags?limit=${limit}`;
    if (status) url += `&status=${status}`;
    if (priority) url += `&priority=${priority}`;

    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) flags.value = data.data;
  } catch (err) {
    console.error("❌ Failed to fetch content flags", err);
  }
}

// ----------------------
// Modal State for Alerts
// ----------------------
const showAddAlertModal = ref(false);
const newAlert = reactive({
  type: "",
  message: "",
  suggested_action: "",
});

// Open / Close
function openAddAlertModal() {
  showAddAlertModal.value = true;
}
function closeAddAlertModal() {
  showAddAlertModal.value = false;
  newAlert.type = "";
  newAlert.message = "";
  newAlert.suggested_action = "";
}

// Submit new Alert -> (if API actually creates "flags", adapt here)
async function submitNewAlert() {
  try {
    const res = await fetch("/api/v1/admin/dashboard/alerts", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(newAlert),
    });
    const data = await res.json();
    if (data.success) {
      closeAddAlertModal();
      fetchAlerts(); // refresh
    } else {
      console.error("❌ Failed to create alert", data.errors || data.message);
    }
  } catch (err) {
    console.error("❌ Error creating alert", err);
  }
}

async function createFlag(flagData) {
  try {
    const res = await fetch("/api/v1/admin/dashboard/flags", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(flagData),
    });
    const data = await res.json();
    if (data.success) {
      fetchFlags(); // Refresh list
    } else {
      console.error("❌ Failed to create flag", data.errors || data.message);
    }
  } catch (err) {
    console.error("❌ Error creating flag", err);
  }
}

// ----------------------
// Lifecycle
// ----------------------
onMounted(() => {
  fetchStats();
  fetchSkillEngagement();
  fetchMoodTrends();
  fetchAlerts();
  fetchFlags();
});
</script>


<style scoped>
h1,
h2 {
  font-family: "Fredoka", sans-serif;
}
</style>
