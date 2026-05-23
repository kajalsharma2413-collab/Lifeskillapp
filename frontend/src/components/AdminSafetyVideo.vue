<template>
  <div class="flex-1 p-10">
    <!-- Safety Videos Section -->
    <div>
      <!-- Video List -->
      <div class="glass-box mb-6">
        <h3 class="text-xl font-bold mb-4">🎥 Existing Safety Videos</h3>
        <div v-for="video in videoList" :key="video.id" class="bg-white/10 border border-white/20 p-4 mb-6 rounded-xl">
          <!-- Thumbnail -->
          <img v-if="video.thumbnail" :src="video.thumbnail" alt="thumbnail"
            class="w-full h-48 object-cover rounded-lg mb-2" />

          <!-- Title + Description -->
          <h4 class="font-semibold text-lg">{{ video.title }}</h4>
          <p class="text-sm text-gray-300">{{ video.description }}</p>

          <!-- Video -->
          <video v-if="video.video_url" controls class="w-full mt-2 rounded-lg" :src="video.video_url"></video>

          <!-- Badge + Quiz Info -->
          <p class="mt-2 text-sm text-gray-400">🏅 Badge ID: {{ video.badge_id }}
            <button class="ml-2 btn-edit" @click="copyId(video.badge_id)">Copy</button>
          </p>
          <p v-if="video.quiz_id" class="text-sm text-gray-400">
            📋 Quiz ID: {{ video.quiz_id }}
            <button class="ml-2 btn-edit" @click="copyId(video.quiz_id)">Copy</button>
          </p>

          <!-- Actions -->
          <div class="mt-2 flex gap-2">
            <button class="btn-edit" @click="openQuiz(video)">✏️ Manage Quiz</button>
            <button class="btn-delete" @click="deleteVideo(video.id)">🗑️ Delete</button>
          </div>
        </div>
      </div>

      <!-- Add Video Form -->
      <div class="glass-box mb-6">
        <h3 class="text-2xl font-bold mb-4">➕ Add Safety Video</h3>
        <form @submit.prevent="addVideo" class="space-y-4">
          <input v-model="videoForm.title" placeholder="Title" class="form-input" required />
          <input v-model="videoForm.description" placeholder="Description" class="form-input" required />
          <input v-model="videoForm.video_url" placeholder="Video URL" class="form-input" />
          <input v-model="videoForm.thumbnail_url" placeholder="Thumbnail URL" class="form-input" required />
          <input v-model="videoForm.badge_id" placeholder="Badge ID" class="form-input" required />
          <button class="btn-submit">Submit Video</button>
        </form>
      </div>

      <!-- Quiz Section -->
      <div v-if="selectedVideo" class="glass-box mb-6">
        <h3 class="text-xl font-bold mb-2">
          📋 Manage Quiz for: <span class="text-accent">{{ selectedVideo.title }}</span>
        </h3>

        <!-- Add Question -->
        <form @submit.prevent="addVideoQuestion" class="space-y-4">
          <input v-model="videoQuestion.question_text" placeholder="Enter question" class="form-input" required />
          <button class="btn-submit">Add Question</button>
        </form>

        <!-- Questions -->
        <div v-if="videoQuiz.questions?.length" class="mt-4 space-y-4">
          <div v-for="(question, qIdx) in videoQuiz.questions" :key="question.id" class="glass-box">
            <h4 class="font-semibold">{{ question.question_text }}</h4>
            <ul class="ml-4 mt-2">
              <li v-for="(opt, oIdx) in question.options" :key="opt.id" class="text-sm"
                :class="opt.is_correct ? 'text-green-400' : 'text-red-400'">
                {{ opt.text }}
              </li>
            </ul>

            <!-- Add Option -->
            <div v-if="currentQuestionId === question.id" class="mt-3">
              <input v-model="videoOption.option_text" placeholder="Option Text" class="form-input inline w-1/2" />
              <select v-model="videoOption.is_correct" class="form-input inline w-1/4 ml-2">
                <option :value="true">Correct</option>
                <option :value="false">Incorrect</option>
              </select>
              <button @click="addVideoOption(question.id)" class="ml-2 btn-submit">Add</button>
              <button @click="doneWithOptions" class="ml-2 btn-done">✅ Done</button>
            </div>
          </div>
        </div>

        <button v-if="currentQuizId" @click="fetchVideoQuiz(currentQuizId)" class="btn-manage mt-4">
          🔄 Refresh Quiz
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const token = localStorage.getItem("firebase_token");
const videoList = ref([]);
const selectedVideo = ref(null);
const videoQuiz = ref({});
const videoForm = ref({
  title: "",
  description: "",
  video_url: "",
  thumbnail_url: "",
  skill_type: "safety",
  badge_id: "",
});

// Question + Option state
const videoQuestion = ref({ question_text: "", question_order: 1 });
const videoOption = ref({ option_text: "", is_correct: false, option_order: 1 });

const currentQuestionId = ref(localStorage.getItem("current_question_id"));
const currentQuizId = ref(localStorage.getItem("current_quiz_id"));

// === API: Fetch Videos ===
async function fetchVideos() {
  try {
    const res = await fetch("/api/v1/safety/videos", {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) videoList.value = data.data.videos || [];
  } catch (err) {
    console.error("❌ Failed to fetch videos", err);
  }
}

// === API: Add Video ===
async function addVideo() {
  try {
    const res = await fetch("/api/v1/admin/safety/video", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(videoForm.value),
    });
    const data = await res.json();
    if (data.success) {
      videoList.value.push(data.data);
      videoForm.value = {
        title: "",
        description: "",
        video_url: "",
        thumbnail_url: "",
        skill_type: "safety",
        badge_id: "",
      };
      alert("✅ Video added!");
    }
  } catch (err) {
    console.error("❌ Error adding video", err);
  }
}

// === API: Delete Video ===
async function deleteVideo(videoId) {
  if (!confirm("Delete this video?")) return;
  try {
    const res = await fetch(`/api/v1/admin/safety/video/${videoId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      videoList.value = videoList.value.filter((v) => v.id !== videoId);
    }
  } catch (err) {
    console.error("❌ Error deleting video", err);
  }
}

// === API: Open Quiz ===
// === API: Open Quiz ===
async function openQuiz(video) {
  selectedVideo.value = video;
  if (video.quiz_id) {
    currentQuizId.value = video.quiz_id;
    localStorage.setItem("current_quiz_id", video.quiz_id);

    // ✅ Attach badge before fetching quiz
    await attachBadgeToQuiz(video.quiz_id, video.badge_id);

    await fetchVideoQuiz(video.quiz_id);
  } else {
    videoQuiz.value = {};
  }
}

// === API: Attach Badge to Quiz ===
async function attachBadgeToQuiz(quizId, badgeId) {
  try {
    const res = await fetch(`/api/v1/admin/admin/quiz/${quizId}/badge?badge_id=${badgeId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });
    const data = await res.json();
    if (data.success) {
      console.log(`✅ Badge ${badgeId} attached to quiz ${quizId}`);
    } else {
      console.error("❌ Failed to attach badge:", data);
    }
  } catch (err) {
    console.error("❌ Error attaching badge to quiz", err);
  }
}


// === API: Fetch Quiz ===
async function fetchVideoQuiz(quizId) {
  try {
    const res = await fetch(`/api/v1/quiz/${quizId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = await res.json();
    if (data.success) {
      videoQuiz.value = data.data;
    }
  } catch (err) {
    console.error("❌ Failed to fetch quiz", err);
  }
}

// === API: Add Question ===
async function addVideoQuestion() {
  if (!selectedVideo.value) return;
  try {
    const res = await fetch(`/api/v1/admin/safety/video/${selectedVideo.value.id}/question`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(videoQuestion.value),
    });
    const data = await res.json();
    console.log("📌 Add Question Response:", data);

    if (data.success) {
      let newQuestionId = null;

      // ✅ check if API returns a single question object
      if (data.data?.question_id) {
        newQuestionId = data.data.question_id;
      }

      if (newQuestionId) {
        localStorage.setItem("current_question_id", newQuestionId);
        currentQuestionId.value = newQuestionId;
      } else {
        console.error("❌ Could not find new question id in response:", data);
      }

      await fetchVideoQuiz(currentQuizId.value);
      videoQuestion.value = {
        question_text: "",
        question_order: (videoQuiz.value.questions?.length || 0) + 1,
      };
    }
  } catch (err) {
    console.error("❌ Error adding question", err);
  }
}
// === API: Add Option ===
async function addVideoOption(questionId) {
  try {
    // find the question in videoQuiz
    const question = videoQuiz.value.questions.find(q => q.id === questionId);
    const lastOrder = question?.options?.length || 0;

    const payload = {
      ...videoOption.value,
      option_order: lastOrder + 1   // ✅ increment order
    };

    const res = await fetch(`/api/v1/admin/safety/video/question/${questionId}/option`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log("📌 Add Option Response:", data);

    if (data.success) {
      await fetchVideoQuiz(currentQuizId.value);
      videoOption.value = { option_text: "", is_correct: false, option_order: 1 };
    }
  } catch (err) {
    console.error("❌ Error adding option", err);
  }
}

// === Done with Options ===
function doneWithOptions() {
  localStorage.removeItem("current_question_id");
  currentQuestionId.value = null;
  alert("✅ Done with options for this question. Add another question now.");
}

// === Copy ID Helper ===
function copyId(id) {
  navigator.clipboard.writeText(id).then(() => {
    alert("📋 ID copied!");
  });
}

onMounted(fetchVideos);
</script>

<style scoped>
.glass-box {
  @apply bg-white/10 border border-white/20 rounded-xl p-6 shadow-xl backdrop-brightness-110;
}
.form-input {
  @apply w-full p-2 rounded border border-gray-300 text-black;
}
.btn-submit {
  @apply bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded font-bold;
}
.btn-done {
  @apply bg-blue-600 text-white px-3 py-1 rounded;
}
.btn-edit {
  @apply bg-yellow-400 text-black px-3 py-1 rounded;
}
.btn-delete {
  @apply bg-red-600 text-white px-3 py-1 rounded;
}
.btn-manage {
  @apply bg-purple-600 text-white px-3 py-1 rounded;
}
</style>