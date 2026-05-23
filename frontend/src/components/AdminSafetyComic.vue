<template>
    <div class="flex-1 p-10">
        <!-- Safety Comics Section -->
        <div>
            <!-- Comic List -->
            <div class="glass-box mb-6">
                <h3 class="text-xl font-bold mb-4">📚 Existing Safety Comics</h3>
                <div v-for="comic in comicList" :key="comic.id"
                    class="bg-white/10 border border-white/20 p-4 mb-6 rounded-xl">
                    <!-- Thumbnail -->
                    <img v-if="comic.thumbnail" :src="comic.thumbnail" alt="thumbnail"
                        class="w-full h-48 object-cover rounded-lg mb-2" />

                    <!-- Title + Description -->
                    <h4 class="font-semibold text-lg">{{ comic.title }}</h4>
                    <p class="text-sm text-gray-300">{{ comic.description }}</p>

                    <!-- Badge + Quiz Info -->
                    <p class="mt-2 text-sm text-gray-400">🏅 Badge ID: {{ comic.badge_id }}
                        <button class="ml-2 btn-edit" @click="copyId(comic.badge_id)">Copy</button>
                    </p>
                    <p v-if="comic.quiz_id" class="text-sm text-gray-400">
                        📋 Quiz ID: {{ comic.quiz_id }}
                        <button class="ml-2 btn-edit" @click="copyId(comic.quiz_id)">Copy</button>
                    </p>

                    <!-- Actions -->
                    <div class="mt-2 flex gap-2">
                        <button class="btn-edit" @click="openQuiz(comic)">✏️ Manage Quiz</button>
                        <button class="btn-delete" @click="deleteComic(comic.id)">🗑️ Delete</button>
                    </div>
                </div>
            </div>

            <!-- Add Comic Form -->
            <div class="glass-box mb-6">
                <h3 class="text-2xl font-bold mb-4">➕ Add Safety Comic</h3>
                <form @submit.prevent="addComic" class="space-y-4">
                    <input v-model="comicForm.title" placeholder="Title" class="form-input" required />
                    <input v-model="comicForm.description" placeholder="Description" class="form-input" required />
                    <input v-model="comicForm.pdf_url" placeholder="PDF URL" class="form-input" required />
                    <input v-model="comicForm.thumbnail_url" placeholder="Thumbnail URL" class="form-input" required />
                    <input v-model="comicForm.badge_id" placeholder="Badge ID" class="form-input" required />
                    <button class="btn-submit">Submit Comic</button>
                </form>
            </div>

            <!-- Quiz Section -->
            <div v-if="selectedComic" class="glass-box mb-6">
                <h3 class="text-xl font-bold mb-2">
                    📋 Manage Quiz for: <span class="text-accent">{{ selectedComic.title }}</span>
                </h3>

                <!-- Add Question -->
                <form @submit.prevent="addComicQuestion" class="space-y-4">
                    <input v-model="comicQuestion.question_text" placeholder="Enter question" class="form-input"
                        required />
                    <button class="btn-submit">Add Question</button>
                </form>

                <!-- Questions -->
                <div v-if="comicQuiz.questions?.length" class="mt-4 space-y-4">
                    <div v-for="question in comicQuiz.questions" :key="question.id" class="glass-box">
                        <h4 class="font-semibold">{{ question.question_text }}</h4>
                        <ul class="ml-4 mt-2">
                            <li v-for="opt in question.options" :key="opt.id" class="text-sm"
                                :class="opt.is_correct ? 'text-green-400' : 'text-red-400'">
                                {{ opt.text }}
                            </li>
                        </ul>

                        <!-- Add Option -->
                        <div v-if="currentQuestionId === question.id" class="mt-3">
                            <input v-model="comicOption.option_text" placeholder="Option Text"
                                class="form-input inline w-1/2" />
                            <select v-model="comicOption.is_correct" class="form-input inline w-1/4 ml-2">
                                <option :value="true">Correct</option>
                                <option :value="false">Incorrect</option>
                            </select>
                            <button @click="addComicOption(question.id)" class="ml-2 btn-submit">Add</button>
                            <button @click="doneWithOptions" class="ml-2 btn-done">✅ Done</button>
                        </div>
                    </div>
                </div>

                <button v-if="currentQuizId" @click="fetchComicQuiz(currentQuizId)" class="btn-manage mt-4">
                    🔄 Refresh Quiz
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const token = localStorage.getItem("firebase_token");
const comicList = ref([]);
const selectedComic = ref(null);
const comicQuiz = ref({});
const comicForm = ref({
    title: "",
    description: "",
    pdf_url: "",
    thumbnail_url: "",
    skill_type: "safety",
    badge_id: "",
});

// Question + Option state
const comicQuestion = ref({ question_text: "", question_order: 1 });
const comicOption = ref({ option_text: "", is_correct: false, option_order: 1 });

const currentQuestionId = ref(localStorage.getItem("current_question_id"));
const currentQuizId = ref(localStorage.getItem("current_quiz_id"));

// === API: Fetch Comics ===
async function fetchComics() {
    try {
        const res = await fetch("/api/v1/safety/comics", {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (data.success) comicList.value = data.data.comics || [];
    } catch (err) {
        console.error("❌ Failed to fetch comics", err);
    }
}
// === API: Assign Badge to Quiz ===
async function assignBadgeToQuiz(quizId, badgeId) {
    try {
        const res = await fetch(`/api/v1/admin/admin/quiz/${quizId}/badge?badge_id=${badgeId}`, {
            method: "PATCH",
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        console.log("📌 Assign Badge Response:", data);

        if (data.success) {
            alert("✅ Badge assigned to quiz!");
            return true;
        } else {
            alert("❌ Failed to assign badge");
        }
    } catch (err) {
        console.error("❌ Error assigning badge", err);
    }
    return false;
}

// === API: Add Comic ===
async function addComic() {
    try {
        const res = await fetch("/api/v1/admin/safety/comic", {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(comicForm.value),
        });
        const data = await res.json();
        if (data.success) {
            comicList.value.push(data.data);
            comicForm.value = {
                title: "",
                description: "",
                pdf_url: "",
                thumbnail_url: "",
                skill_type: "safety",
                badge_id: "",
            };
            alert("✅ Comic added!");
        }
    } catch (err) {
        console.error("❌ Error adding comic", err);
    }
}

// === API: Delete Comic ===
async function deleteComic(comicId) {
    if (!confirm("Delete this comic?")) return;
    try {
        const res = await fetch(`/api/v1/admin/safety/comic/${comicId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (data.success) {
            comicList.value = comicList.value.filter((c) => c.id !== comicId);
        }
    } catch (err) {
        console.error("❌ Error deleting comic", err);
    }
}

// === API: Open Quiz ===
async function openQuiz(comic) {
    selectedComic.value = comic;
    if (comic.quiz_id) {
        currentQuizId.value = comic.quiz_id;
        localStorage.setItem("current_quiz_id", comic.quiz_id);

        // ✅ Assign badge before fetching quiz
        if (comic.badge_id) {
            await assignBadgeToQuiz(comic.quiz_id, comic.badge_id);
        }

        await fetchComicQuiz(comic.quiz_id);
    } else {
        comicQuiz.value = {};
    }
}

// === API: Fetch Quiz ===
async function fetchComicQuiz(quizId) {
    try {
        const res = await fetch(`/api/v1/quiz/${quizId}`, {
            headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json();
        if (data.success) {
            comicQuiz.value = data.data;
        }
    } catch (err) {
        console.error("❌ Failed to fetch quiz", err);
    }
}

// === API: Add Question ===
async function addComicQuestion() {
    if (!selectedComic.value) return;
    try {
        const res = await fetch(`/api/v1/admin/safety/comic/${selectedComic.value.id}/question`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(comicQuestion.value),
        });
        const data = await res.json();
        console.log("📌 Add Question Response:", data);

        if (data.success) {
            let newQuestionId = null;

            if (data.data?.question_id) {
                newQuestionId = data.data.question_id;
            }

            if (newQuestionId) {
                localStorage.setItem("current_question_id", newQuestionId);
                currentQuestionId.value = newQuestionId;
            } else {
                console.error("❌ Could not find new question id in response:", data);
            }

            await fetchComicQuiz(currentQuizId.value);
            comicQuestion.value = {
                question_text: "",
                question_order: (comicQuiz.value.questions?.length || 0) + 1,
            };
        }
    } catch (err) {
        console.error("❌ Error adding question", err);
    }
}

// === API: Add Option ===
async function addComicOption(questionId) {
    try {
        const question = comicQuiz.value.questions.find(q => q.id === questionId);
        const lastOrder = question?.options?.length || 0;

        const payload = {
            ...comicOption.value,
            option_order: lastOrder + 1
        };

        const res = await fetch(`/api/v1/admin/safety/comic/question/${questionId}/option`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
            body: JSON.stringify(payload),
        });
        const data = await res.json();
        console.log("📌 Add Option Response:", data);

        if (data.success) {
            await fetchComicQuiz(currentQuizId.value);
            comicOption.value = { option_text: "", is_correct: false, option_order: 1 };
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

onMounted(fetchComics);
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