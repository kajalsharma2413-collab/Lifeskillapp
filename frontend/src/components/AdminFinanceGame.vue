<template>
  <div class="flex-1 p-10">
    <!-- Add Level -->
    <div class="glass-box mb-6">
      <h3 class="text-2xl font-bold mb-4">➕ Add Finance Level</h3>
      <form @submit.prevent="addLevel" class="space-y-4">
        <input v-model="levelForm.level_number" type="number" placeholder="Level Number" class="form-input" required />
        <input v-model="levelForm.title" placeholder="Level Title" class="form-input" required />
        <textarea v-model="levelForm.description" placeholder="Description" class="form-textarea" required></textarea>
        <input v-model="levelForm.income" type="number" placeholder="Monthly Income" class="form-input" required />
        <select v-model="levelForm.difficulty" class="form-input">
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <button class="btn-submit">Add Level</button>
      </form>
    </div>

    <!-- Level List -->
    <div v-for="level in levels" :key="level.id" class="glass-box mb-6">
      <div class="flex justify-between">
        <h4 class="text-xl font-bold">Level {{ level.level_number }} - {{ level.title }}</h4>
        <div class="flex gap-2">
          <button class="btn-delete" @click="deleteLevel(level.id)">Delete</button>
        </div>
      </div>
      <p class="text-gray-300">{{ level.description }}</p>
      <p class="text-sm">💰 Income: {{ level.income }} | 🎯 Difficulty: {{ level.difficulty }}</p>

      <!-- Quiz ID -->
      <div v-if="level.quiz_id" class="mt-2">
        🎯 Quiz ID:
        <span class="font-mono bg-gray-700 px-2 py-1 rounded">{{ level.quiz_id }}</span>
        <button class="btn-edit ml-2" @click="copyId(level.quiz_id)">📋 Copy</button>
      </div>

      <!-- Add Level Item -->
      <form @submit.prevent="addLevelItem(level.id)" class="mt-4 space-y-2">
        <input v-model="levelItem.name" placeholder="Item Name" class="form-input" required />
        <input v-model="levelItem.cost" type="number" placeholder="Cost" class="form-input" required />
        <input v-model="levelItem.description" placeholder="Item Description" class="form-input" />
        <select v-model="levelItem.item_type" class="form-input" required>
          <option disabled value="">Select Item Type</option>
          <option value="need">Need</option>
          <option value="want">Want</option>
        </select>
        <button class="btn-submit">Add Item</button>
      </form>

      <!-- Items -->
      <div v-if="level.items && level.items.length" class="mt-3">
        <h5 class="font-semibold text-lg">📦 Items</h5>
        <div v-for="item in level.items" :key="item.name" class="mt-2 bg-white/10 p-3 rounded">
          <div class="flex justify-between items-center">
            <p>
              {{ item.name }} - 💰 {{ item.cost }} | {{ item.item_type }}
              <span class="text-gray-400">({{ item.description }})</span>
            </p>
          </div>
        </div>
      </div>
      <div v-else class="text-gray-400 mt-2">⚠️ No items added yet.</div>

      <!-- Finalize Level -->
      <button class="btn-submit mt-4" @click="finalizeLevel(level.id)">✅ Finalize Level</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const token = localStorage.getItem("firebase_token");
const levels = ref([]);

const levelForm = ref({
  level_number: 1,
  title: "",
  description: "",
  income: 100,
  difficulty: "easy",
});

const levelItem = ref({
  name: "",
  cost: 0,
  item_type: "",
  description: "",
});

// === API: Get Levels with items ===
async function fetchLevels() {
  try {
    const res = await fetch("/api/v1/admin/finance/levels", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();

    if (data.success) {
      const rawLevels = data.data.levels || [];

      const levelsWithItems = await Promise.all(
        rawLevels.map(async (level) => {
          try {
            const res2 = await fetch(`/api/v1/finance/game/level/${level.level_number}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            const gameData = await res2.json();

            if (gameData.success) {
              return {
                ...level,
                income: gameData.data.income,
                items: gameData.data.items || [],
                quiz_id: gameData.data.quiz_id,
              };
            }
          } catch (err) {
            console.error(`❌ Failed to fetch items for level ${level.level_number}`, err);
          }
          return { ...level, items: [] };
        })
      );

      levels.value = levelsWithItems;
    }
  } catch (err) {
    console.error("❌ Failed to fetch finance levels", err);
  }
}

// === API: Add Level ===
async function addLevel() {
  try {
    const res = await fetch("/api/v1/admin/finance/level", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(levelForm.value),
    });
    const data = await res.json();
    console.log("📌 Add Level Response:", data);
    if (data.success) {
      alert("✅ Finance Level created! Refreshing...");
      await fetchLevels(); // reload with items
      levelForm.value = {
        level_number: levelForm.value.level_number + 1,
        title: "",
        description: "",
        income: 100,
        difficulty: "easy",
      };
    }
  } catch (err) {
    console.error("❌ Error adding level", err);
  }
}

// === API: Delete Level ===
async function deleteLevel(levelId) {
  if (!confirm("Delete this level?")) return;
  try {
    const res = await fetch(`/api/v1/admin/finance/level/${levelId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    console.log("📌 Delete Level Response:", data);
    if (data.success) {
      levels.value = levels.value.filter((l) => l.id !== levelId);
    }
  } catch (err) {
    console.error("❌ Error deleting level", err);
  }
}

// === API: Add Level Item ===
async function addLevelItem(levelId) {
  try {
    const res = await fetch(`/api/v1/admin/finance/level/${levelId}/item`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(levelItem.value),
    });
    const data = await res.json();
    console.log("📌 Add Item Response:", data);

    if (data.success) {
      // Refresh levels to update items
      await fetchLevels();
      levelItem.value = { name: "", cost: 0, item_type: "", description: "" };
      alert("✅ Item added successfully!");
    } else {
      alert("⚠️ Failed to add item: " + (data.message || "Unknown error"));
    }
  } catch (err) {
    console.error("❌ Error adding level item", err);
    alert("❌ Error adding item, check console");
  }
}
// === Finalize Level ===
async function finalizeLevel(levelId) {
  alert(`✅ Level ${levelId} finalized!`);
}

// === Copy Quiz ID ===
function copyId(id) {
  navigator.clipboard.writeText(id).then(() => {
    alert("📋 Quiz ID copied!");
  });
}

onMounted(fetchLevels);
</script>

<style scoped>
.glass-box {
  @apply bg-white/10 border border-white/20 rounded-xl p-6 shadow-xl backdrop-brightness-110;
}
.form-input {
  @apply w-full p-2 rounded border border-gray-300 text-black;
}
.form-textarea {
  @apply w-full p-2 h-24 rounded border border-gray-300 text-black;
}
.btn-submit {
  @apply bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded font-bold;
}
.btn-delete {
  @apply bg-red-600 text-white px-3 py-1 rounded;
}
.btn-edit {
  @apply bg-yellow-400 text-black px-3 py-1 rounded;
}
</style>
