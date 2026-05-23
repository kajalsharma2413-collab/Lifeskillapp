<template>
  <div class="flex min-h-screen">
    <!-- Sidebar -->
    <div class="w-64 bg-background-paper shadow-elevated p-4">
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
      <!-- Create Badge -->
      <div class="glass-box mb-6">
        <h3 class="text-2xl font-bold mb-4">➕ Create Badge</h3>
        <form @submit.prevent="createBadge" class="space-y-4">
          <input v-model="badgeForm.badge_name" placeholder="Badge Name" class="form-input" required />
          <input v-model="badgeForm.badge_url" placeholder="Badge Image URL" class="form-input" required />
          <textarea v-model="badgeForm.description" placeholder="Description" class="form-textarea"></textarea>
          <select v-model="badgeForm.skill_type" class="form-input" required>
            <option disabled value="">Select Skill Type</option>
            <option value="safety">Safety</option>
            <option value="finance">Finance</option>
            <option value="communication">Communication</option>
            <option value="problem_solving">Problem Solving</option>
            <option value="basic_manners">Basic Manners</option>
          </select>
          <input v-model="badgeForm.points" type="number" min="1" placeholder="Points" class="form-input" required />
          <button class="btn-submit">Create Badge</button>
        </form>
      </div>

      <!-- Badge List -->
      <div class="glass-box">
        <h3 class="text-2xl font-bold mb-4">🏅 Existing Badges</h3>
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="border-b border-gray-500 text-sm text-gray-300">
              <th class="p-2">Image</th>
              <th class="p-2">Name</th>
              <th class="p-2">Skill</th>
              <th class="p-2">Points</th>
              <th class="p-2">Badge ID</th>
              <th class="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="badge in badges" :key="badge.id" class="border-b border-gray-700">
              <td class="p-2">
                <img :src="badge.image_url" alt="badge" class="h-12 w-12 rounded object-cover" />
              </td>
              <td class="p-2 font-semibold">{{ badge.name }}</td>
              <td class="p-2">{{ badge.skill_type }}</td>
              <td class="p-2">{{ badge.points }}</td>
              <td class="p-2 text-xs text-gray-400">{{ badge.id }}</td>
              <td class="p-2 flex gap-2">
                <button class="btn-edit" @click="copyId(badge.id)">📋 Copy ID</button>
                <button class="btn-delete" @click="deleteBadge(badge.id)">🗑️ Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const token = localStorage.getItem("firebase_token");
const badges = ref([]);

const badgeForm = ref({
  badge_name: "",
  badge_url: "",
  description: "",
  skill_type: "",
  points: 5,
});

// === API: Get All Badges (Public) ===
async function fetchBadges() {
  try {
    const res = await fetch("/api/v1/public/badges");
    const data = await res.json();
    if (data.success) badges.value = data.data.badges || [];
  } catch (err) {
    console.error("❌ Failed to fetch badges", err);
  }
}

// === API: Create Badge ===
async function createBadge() {
  try {
    const res = await fetch("/api/v1/admin/badges", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(badgeForm.value),
    });
    const data = await res.json();
    if (data.success) {
      badges.value.push(data.data);
      badgeForm.value = { badge_name: "", badge_url: "", description: "", skill_type: "", points: 5 };
      alert("✅ Badge created!");
    }
  } catch (err) {
    console.error("❌ Error creating badge", err);
  }
}

// === API: Delete Badge ===
async function deleteBadge(badgeId) {
  if (!confirm("Delete this badge?")) return;
  try {
    const res = await fetch(`/api/v1/admin/badges/${badgeId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      badges.value = badges.value.filter((b) => b.id !== badgeId);
    }
  } catch (err) {
    console.error("❌ Error deleting badge", err);
  }
}

// === Copy Badge ID ===
function copyId(id) {
  navigator.clipboard.writeText(id).then(() => {
    alert("📋 Badge ID copied!");
  });
}

onMounted(fetchBadges);
</script>

<style scoped>
.glass-box {
  @apply bg-white/10 border border-white/20 rounded-xl p-6 shadow-xl backdrop-brightness-110;
}
.form-input {
  @apply w-full p-2 rounded border border-gray-300 text-black;
}
.form-textarea {
  @apply w-full p-2 h-20 rounded border border-gray-300 text-black;
}
.btn-submit {
  @apply bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded font-bold;
}
.btn-edit {
  @apply bg-yellow-400 text-black px-3 py-1 rounded;
}
.btn-delete {
  @apply bg-red-600 text-white px-3 py-1 rounded;
}
</style>
