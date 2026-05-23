<template>
    <div>
        <!-- Floating Button -->
        <div class="fixed bottom-6 right-6 z-50 group">
            <button @click="openChat"
                class="w-14 h-14 bg-accent text-black rounded-full shadow-lg hover:scale-105 transition-all flex items-center justify-center relative">
                💬
                <span
                    class="absolute bottom-full mb-2 text-sm bg-black/80 text-white py-1 px-2 rounded shadow opacity-0 group-hover:opacity-100 transition">
                    Ask AI about this comic
                </span>
            </button>
        </div>

        <!-- Modal -->
        <div v-if="show" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex justify-center items-center px-6">
            <div class="relative w-full max-w-6xl h-[90vh] bg-cover bg-center rounded-2xl overflow-hidden shadow-2xl"
                :style="`background-image: url('/src/assets/aeed5846-1bb4-4519-9db8-48217e1a4d98.png');`">
                <!-- Overlay -->
                <div class="absolute inset-0 bg-black/70 backdrop-blur-sm"></div>

                <div class="relative z-10 p-6 h-full flex flex-col text-white">
                    <!-- Header -->
                    <h2 class="text-3xl font-bold text-accent text-center mb-6 flex justify-between items-center">
                        <span>💬 Comic Chatbot</span>
                        <div class="flex gap-2">
                            <button @click="newChat"
                                class="px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm rounded-full transition">
                                New Chat
                            </button>
                            <button v-if="typingInProgress" @click="stopTyping"
                                class="px-4 py-2 bg-yellow-500 hover:bg-yellow-400 text-black text-sm rounded-full transition">
                                Stop
                            </button>
                            <button @click="closeChat"
                                class="px-4 py-2 bg-gray-500 hover:bg-gray-400 text-white text-sm rounded-full transition">
                                ✖
                            </button>
                        </div>
                    </h2>

                    <!-- Messages -->
                    <div class="flex-1 overflow-y-auto pr-3 space-y-4 bg-black/30 rounded-xl p-6 shadow-inner">
                        <div v-for="(msg, i) in messages" :key="i"
                            :class="msg.sender === 'ai' ? 'text-left text-accent-light' : 'text-right text-green-300'">
                            <p :class="msg.sender === 'ai'
                                ? 'bg-white/10 p-4 rounded-2xl inline-block max-w-[80%] leading-relaxed'
                                : 'bg-green-600/30 p-4 rounded-2xl inline-block max-w-[80%] leading-relaxed ml-auto'">
                                {{ msg.text }}
                            </p>
                        </div>

                        <!-- Loading Spinner -->
                        <div v-if="loading && !typingInProgress" class="text-left text-white">
                            <p class="bg-white/10 px-4 py-2 rounded-2xl inline-block animate-pulse">
                                🤖 Typing...
                            </p>
                        </div>
                    </div>

                    <!-- Input -->
                    <form @submit.prevent="sendMessage" class="mt-4 flex gap-3 bg-black/40 rounded-full p-3">
                        <input v-model="inputMessage" type="text" required placeholder="Type your message..."
                            class="flex-1 px-5 py-3 bg-transparent text-white placeholder-white/60 rounded-full outline-none focus:ring-2 ring-accent" />
                        <button type="submit"
                            class="px-6 py-3 bg-accent text-black font-bold rounded-full hover:bg-accent-light transition">
                            Send
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from "vue";

const show = ref(false);
const inputMessage = ref("");
const messages = ref([]);
const loading = ref(false);
let typingInProgress = false;
let stopRequested = false;
let sessionId = ref(localStorage.getItem("chat_session_id") || null);
let comicTitle = ref("");
let firstMessage = true;

function closeChat() {
    show.value = false;
}

function newChat() {
    messages.value = [
        {
            text: "👋 Hi! Please tell me the comic title so I can start helping you.",
            sender: "ai",
        },
    ];
    sessionId.value = null;
    localStorage.removeItem("chat_session_id");
    comicTitle.value = "";
    firstMessage = true;
}

function openChat() {
    show.value = true;
    newChat();
}

async function typewriterEffect(fullText) {
    typingInProgress = true;
    stopRequested = false;
    let currentText = "";
    for (let i = 0; i < fullText.length; i++) {
        if (stopRequested) {
            currentText = fullText;
            break;
        }
        currentText += fullText[i];
        messages.value[messages.value.length - 1].text = currentText;
        await new Promise((resolve) => setTimeout(resolve, 25));
    }
    messages.value[messages.value.length - 1].text = fullText;
    typingInProgress = false;
}

function stopTyping() {
    stopRequested = true;
}

async function sendMessage() {
    const message = inputMessage.value.trim();
    if (!message || typingInProgress) return;

    messages.value.push({ text: message, sender: "user" });
    inputMessage.value = "";
    loading.value = true;

    try {
        const token = localStorage.getItem("firebase_token");

        let finalMessage;
        if (firstMessage) {
            comicTitle.value = message;
            finalMessage = `Start chat for comic: ${comicTitle.value}`;
            firstMessage = false;
        } else {
            finalMessage = message;
        }

        const res = await fetch("/api/v1/rag_chat/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({
                question: finalMessage,
                session_id: sessionId.value || null,
            }),
        });

        const data = await res.json();
        loading.value = false;

        if (!sessionId.value && data.session_id) {
            sessionId.value = data.session_id;
            localStorage.setItem("chat_session_id", sessionId.value);
        }

        if (data.answer) {
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
</script>
