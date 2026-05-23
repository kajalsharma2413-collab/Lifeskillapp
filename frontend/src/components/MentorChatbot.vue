<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
    session: {
        type: Object,
        required: true // { session_id, initial_response }
    },
    show: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['close'])

const messages = ref([])
const userInput = ref('')
const loading = ref(false)

// Typewriter effect helper
const typeWriter = async (text) => {
    let displayed = ''
    for (let i = 0; i < text.length; i++) {
        displayed += text[i]
        messages.value[messages.value.length - 1].text = displayed
        await new Promise(r => setTimeout(r, 25)) // typing speed
    }
}

// Reset messages when session changes
watch(
    () => props.session,
    (newSession) => {
        if (newSession?.initial_response) {
            messages.value = [
                { sender: 'mentor', text: '' }
            ]
            typeWriter(newSession.initial_response)
        }
    },
    { immediate: true }
)

const sendMessage = async () => {
    if (!userInput.value.trim() || loading.value) return

    const question = userInput.value
    messages.value.push({ sender: 'user', text: question })
    userInput.value = ''
    loading.value = true

    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch('/api/v1/mentor/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${token}`
            },
            body: JSON.stringify({
                question,
                session_id: props.session.session_id
            })
        })
        const data = await res.json()

        if (res.ok && data.answer) {
            messages.value.push({ sender: 'mentor', text: '' }) // placeholder
            await typeWriter(data.answer)
        } else {
            messages.value.push({
                sender: 'mentor',
                text: '⚠️ Mentor could not answer. Please try again.'
            })
        }
    } catch (err) {
        console.error('❌ Mentor chat error', err)
        messages.value.push({
            sender: 'mentor',
            text: '❌ Something went wrong while chatting with mentor.'
        })
    } finally {
        loading.value = false
    }
}
</script>

<template>
    <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div
            class="bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl shadow-xl w-full max-w-lg h-[80vh] flex flex-col">

            <!-- Header -->
            <div class="p-4 flex justify-between items-center border-b border-white/20">
                <h2 class="text-xl font-bold text-purple-300">👨‍🏫 Mentor Chat</h2>
                <button @click="emit('close')" class="text-white hover:text-red-400 text-lg font-bold">✖</button>
            </div>

            <!-- Messages -->
            <div class="flex-1 overflow-y-auto p-4 space-y-3">
                <div v-for="(msg, index) in messages" :key="index"
                    :class="msg.sender === 'user' ? 'text-right' : 'text-left'">
                    <div :class="[
                        'inline-block px-4 py-2 rounded-2xl max-w-[75%] whitespace-pre-wrap',
                        msg.sender === 'user'
                            ? 'bg-purple-600 text-white rounded-br-none'
                            : 'bg-white/20 text-white rounded-bl-none'
                    ]">
                        {{ msg.text }}
                    </div>
                </div>

                <div v-if="loading" class="text-center text-white/60">⌛ Mentor is thinking...</div>
            </div>

            <!-- Input -->
            <div class="p-4 border-t border-white/20 flex gap-2">
                <input v-model="userInput" @keyup.enter="sendMessage" type="text" placeholder="Ask something..."
                    class="flex-1 p-2 rounded-lg border border-white/30 bg-white/10 text-white focus:ring-2 focus:ring-purple-500 focus:outline-none" />
                <button @click="sendMessage"
                    class="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg font-semibold">
                    ➤
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 3px;
}
</style>
