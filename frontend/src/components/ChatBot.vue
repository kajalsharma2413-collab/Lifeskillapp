<template>
    <div class="flex min-h-screen text-white">
        <!-- Sidebar -->
        <Sidebar />

        <!-- Chat Content -->
        <div class="flex-1 bg-cover bg-center relative"
            :style="`background-image: url('/src/assets/aeed5846-1bb4-4519-9db8-48217e1a4d98.png');`">
            <!-- Overlay -->
            <div class="absolute inset-0 bg-black/70 backdrop-blur-sm"></div>

            <div class="relative z-10 max-w-2xl mx-auto h-screen py-10 flex flex-col">
                <!-- Header -->
                <h2 class="text-2xl font-bold text-accent text-center mb-6 flex justify-between items-center">
                    <span>💬 Chat with AI</span>
                    <div class="flex gap-2">
                        <button @click="newChat"
                            class="ml-4 px-3 py-1 bg-red-600 hover:bg-red-500 text-white text-sm rounded-full transition">
                            New Chat
                        </button>
                        <button v-if="typingInProgress" @click="stopTyping"
                            class="px-3 py-1 bg-yellow-500 hover:bg-yellow-400 text-black text-sm rounded-full transition">
                            Stop
                        </button>
                    </div>
                </h2>

                <!-- Message Area -->
                <div class="flex-1 overflow-y-auto pr-2 space-y-3">
                    <div v-for="(msg, i) in messages" :key="i" :class="msg.sender === 'ai'
                        ? 'text-left text-accent-light'
                        : 'text-right text-green-300'
                        ">
                        <p class="bg-white/10 p-4 rounded-xl inline-block max-w-[80%] leading-relaxed">
                            {{ msg.text }}
                        </p>
                    </div>
                </div>

                <!-- Loading Spinner -->
                <div v-if="loading && !typingInProgress" class="text-center text-white mt-4">
                    🤖 Typing...
                </div>

                <!-- Input -->
                <form @submit.prevent="sendMessage" class="mt-4 flex gap-2">
                    <input v-model="inputMessage" type="text" required placeholder="Ask me anything!"
                        class="flex-1 px-4 py-2 bg-white/20 text-white placeholder-white/70 rounded-full outline-none focus:ring-2 ring-accent" />
                    <button type="submit"
                        class="px-4 py-2 bg-accent text-black font-bold rounded-full hover:bg-accent-light transition">
                        Send
                    </button>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Sidebar from "@/components/SideBar.vue";

const inputMessage = ref("");
const messages = ref([]);
const loading = ref(false);
let typingInProgress = false;
let stopRequested = false;
let fullTextBuffer = ""; // store the full AI response

// Load session from localStorage if exists
const sessionId = ref(localStorage.getItem("chat_session_id") || null);

const fallbackChat = [
    {
        text: "Hi there! I'm your friendly AI. Ask me anything you want!",
        sender: "ai",
    },
];

onMounted(() => {
    messages.value = fallbackChat;
});

async function typewriterEffect(fullText) {
    typingInProgress = true;
    stopRequested = false;
    fullTextBuffer = fullText;

    let currentText = "";
    for (let i = 0; i < fullText.length; i++) {
        if (stopRequested) {
            // If stop pressed, fill with full text immediately
            currentText = fullText;
            break;
        }
        currentText += fullText[i];
        messages.value[messages.value.length - 1].text = currentText;
        await new Promise((resolve) => setTimeout(resolve, 30)); // typing speed
    }

    messages.value[messages.value.length - 1].text = fullText;
    typingInProgress = false;
}

// Stop button handler
function stopTyping() {
    stopRequested = true;
    if (fullTextBuffer) {
        messages.value[messages.value.length - 1].text = fullTextBuffer;
    }
    typingInProgress = false;
}

async function sendMessage() {
    const message = inputMessage.value.trim();
    if (!message || typingInProgress) return;

    messages.value.push({ text: message, sender: "user" });
    inputMessage.value = "";
    loading.value = true;

    try {
        const token = localStorage.getItem("firebase_token");

        const res = await fetch("/api/v1/rag_chat/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
                question: message,
                session_id: sessionId.value || null,
            }),
        });

        const data = await res.json();
        loading.value = false;

        if (data.answer) {
            // Save session id if new
            if (!sessionId.value && data.session_id) {
                sessionId.value = data.session_id;
                localStorage.setItem("chat_session_id", sessionId.value);
            }

            messages.value.push({ text: "", sender: "ai" });
            await typewriterEffect(data.answer);
        } else {
            messages.value.push({
                text: "⚠️ AI couldn't respond. Please try again.",
                sender: "ai",
            });
        }
    } catch (e) {
        loading.value = false;
        messages.value.push({ text: "⚠️ Error talking to AI.", sender: "ai" });
    }
}

// Start new chat: clear history + session
function newChat() {
    messages.value = fallbackChat;
    sessionId.value = null;
    localStorage.removeItem("chat_session_id");
}
</script>
