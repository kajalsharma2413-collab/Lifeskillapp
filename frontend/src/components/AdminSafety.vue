<template>
  <div class="flex bg-center min-h-screen text-white">
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
    <div class="flex-1 p-10">
      <h2 class="text-4xl font-bold text-center text-yellow-400 mb-10">🦺 Manage Safety Content</h2>

      <!-- Action Toggle -->
      <div class="flex justify-center gap-6 mb-10">
        <button @click="activeTab = 'videos'" :class="tabButton('videos')">📹 Safety Videos</button>
        <button @click="activeTab = 'comics'" :class="tabButton('comics')">📖 Safety Comics</button>
      </div>

      <!-- Show only one component at a time -->
      <AdminSafetyVideo v-if="activeTab === 'videos'" />
      <AdminSafetyComic v-if="activeTab === 'comics'" />
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import AdminSafetyVideo from "./AdminSafetyVideo.vue";
import AdminSafetyComic from "./AdminSafetyComic.vue";

const activeTab = ref("videos");

function tabButton(tab) {
  return `px-6 py-3 rounded-xl font-bold shadow-lg ${activeTab.value === tab
    ? "bg-accent text-black"
    : "bg-white/20 text-white hover:bg-white/30"}`;
}
</script>
