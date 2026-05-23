<template>
    <div class="flex min-h-screen bg-[url('/bg-night-sky.jpg')] bg-cover bg-center text-white">
        <Sidebar />

        <div class="flex-1 p-6 overflow-y-auto">
            <div class="max-w-4xl mx-auto">
                <!-- Avatar and Basic Info -->
                <div class="glass-box flex flex-col items-center mb-8">
                    <img :src="user.avatar_url || `https://api.dicebear.com/9.x/big-smile/svg?seed=${user.username || 'guest'}`"
                        alt="avatar" class="w-24 h-24 rounded-full shadow mb-4 object-cover" />
                    <label class="text-xs text-accent underline cursor-pointer" @click="editing = true">
                        Edit Profile
                    </label>
                    <h2 class="text-3xl font-bold">{{ user.first_name }} {{ user.last_name || '' }}</h2>
                    <p class="text-gray-300">Explorer of Life Skills</p>
                    <p class="text-sm">Age {{ user.age }} | Grade {{ user.grade_level }}</p>
                </div>

                <!-- Badges Section -->
                <div class="glass-box mb-8">
                    <h3 class="text-xl font-bold mb-4">🎖️ Badges</h3>
                    <div v-if="badges.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div v-for="(badge, i) in badges" :key="i"
                            class="bg-white/10 backdrop-blur-md border border-white/20 p-4 rounded-xl flex flex-col items-center text-center">
                            <img :src="badge.image || fallbackIcon" alt="badge" class="h-16 w-16 mb-2" />
                            <span class="font-semibold text-white">{{ badge.name }}</span>
                        </div>
                    </div>
                    <p v-else class="text-sm text-gray-400">No badges earned yet.</p>
                </div>

                <!-- Profile Fields -->
                <div class="glass-box space-y-6">
                    <div>
                        <h4 class="font-semibold mb-1">📧 Email</h4>
                        <p>{{ user.email }}</p>
                    </div>

                    <div>
                        <h4 class="font-semibold mb-1">🎓 Grade Level</h4>
                        <p>{{ user.grade_level }}</p>
                    </div>

                    <div>
                        <h4 class="font-semibold mb-1">🎯 Points</h4>
                        <p>{{ user.points }}</p>
                    </div>
                </div>

                <!-- Edit Profile Modal -->
                <div v-if="editing" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                    <div class="bg-white p-6 rounded-xl max-w-md w-full text-black">
                        <h3 class="text-lg font-semibold mb-4">Edit Profile</h3>

                        <label class="block text-sm mb-1">Username</label>
                        <input v-model="form.username" class="border w-full px-3 py-1 mb-3 rounded" />

                        <label class="block text-sm mb-1">First Name</label>
                        <input v-model="form.first_name" class="border w-full px-3 py-1 mb-3 rounded" />

                        <label class="block text-sm mb-1">Last Name</label>
                        <input v-model="form.last_name" class="border w-full px-3 py-1 mb-3 rounded" />

                        <label class="block text-sm mb-1">Age</label>
                        <input type="number" v-model="form.age" class="border w-full px-3 py-1 mb-3 rounded" />

                        <label class="block text-sm mb-1">Grade Level</label>
                        <select v-model="form.grade_level" required
                            class="input bg-neutral-dark text-white w-full px-3 py-2 mb-3 rounded">
                            <option value="" class="text-black">Select Grade</option>
                            <option value="I" class="text-black">I</option>
                            <option value="II" class="text-black">II</option>
                            <option value="III" class="text-black">III</option>
                            <option value="IV" class="text-black">IV</option>
                            <option value="V" class="text-black">V</option>
                            <option value="VI" class="text-black">VI</option>
                            <option value="VII" class="text-black">VII</option>
                            <option value="VIII" class="text-black">VIII</option>
                        </select>

                        <label class="block text-sm mb-1">Avatar</label>
                        <div class="flex items-center justify-between mb-3">
                            <button @click="prevAvatar" class="px-2 text-lg">⬅️</button>
                            <img :src="form.avatar_url" alt="avatar preview" class="w-20 h-20 rounded-full shadow" />
                            <button @click="nextAvatar" class="px-2 text-lg">➡️</button>
                        </div>

                        <div class="flex justify-end gap-2 mt-4">
                            <button @click="editing = false" class="text-gray-600 hover:underline">Cancel</button>
                            <button @click="saveProfile"
                                class="bg-accent text-white px-4 py-2 rounded font-semibold">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup>
import Sidebar from '@/components/SideBar.vue'
import { ref, onMounted } from 'vue'

const fallbackIcon = '/badges/default.png'
const editing = ref(false)

const user = ref({})
const badges = ref([])
const form = ref({})

// Dicebear avatar seeds
const avatarSeeds = ['Explorer', 'Adventurer', 'Hero', 'Dreamer', 'Champion', 'Star', 'Phoenix']
const avatarIndex = ref(0)

// Helper to get avatar URL
const getAvatarUrl = (seed) => `https://api.dicebear.com/9.x/big-smile/svg?seed=${seed}`

// ✅ Fetch current user info
const fetchUser = async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch('/api/v1/users/me', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        })
        const data = await res.json()
        if (res.ok && data.success) {
            const apiUser = data.data.user

            // Split full name into first and last
            const nameParts = apiUser.name ? apiUser.name.split(' ') : []
            const firstName = nameParts[0] || ''
            const lastName = nameParts.slice(1).join(' ') || ''

            user.value = {
                ...apiUser,
                first_name: firstName,
                last_name: lastName,
                grade_level: apiUser.grade, // map grade → grade_level for UI
            }

            // Preload form for editing
            form.value = {
                username: apiUser.username,
                first_name: firstName,
                last_name: lastName,
                age: apiUser.age,
                grade_level: apiUser.grade,
                avatar_url: apiUser.avatar_url || getAvatarUrl(avatarSeeds[0]),
            }

            // If user already has avatar, sync index
            if (apiUser.avatar_url) {
                const foundIndex = avatarSeeds.findIndex(seed => apiUser.avatar_url.includes(seed))
                avatarIndex.value = foundIndex >= 0 ? foundIndex : 0
            }

            // After fetching user, fetch badges
            fetchBadges()
        }
    } catch (err) {
        console.error('❌ Failed to load user:', err)
    }
}

// ✅ Fetch badges from scoring-table API
const fetchBadges = async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch('/api/v1/users/scoring-table', {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        })
        const data = await res.json()
        if (res.ok && data.success) {
            badges.value = data.data.badges_earned.map(b => ({
                name: b.name,
                image: b.image_url || fallbackIcon,
                description: b.description,
                points: b.points,
            }))
        } else {
            console.warn('⚠️ Failed to fetch badges:', data.message)
        }
    } catch (err) {
        console.error('❌ Error fetching badges:', err)
    }
}

// ✅ Change avatar with arrows
const prevAvatar = () => {
    avatarIndex.value = (avatarIndex.value - 1 + avatarSeeds.length) % avatarSeeds.length
    form.value.avatar_url = getAvatarUrl(avatarSeeds[avatarIndex.value])
}
const nextAvatar = () => {
    avatarIndex.value = (avatarIndex.value + 1) % avatarSeeds.length
    form.value.avatar_url = getAvatarUrl(avatarSeeds[avatarIndex.value])
}

// ✅ Save profile (PUT)
const saveProfile = async () => {
    try {
        const token = localStorage.getItem('firebase_token')
        const res = await fetch(`/api/v1/users/profile/${user.value.id}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: form.value.username,
                first_name: form.value.first_name,
                last_name: form.value.last_name,
                age: form.value.age,
                grade_level: form.value.grade_level,
                avatar_url: form.value.avatar_url,
                preferences: {},
                date_of_birth: null,
            }),
        })

        const data = await res.json()
        if (res.ok && data.success) {
            alert('✅ Profile updated successfully')
            editing.value = false
            fetchUser() // refresh UI
        } else {
            alert('⚠️ Failed to update profile')
        }
    } catch (err) {
        console.error('❌ Error saving profile:', err)
    }
}

onMounted(fetchUser)
</script>


<style scoped>
.bg-accent {
    @apply bg-purple-600;
}

.glass-box {
    @apply bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-6 shadow-lg mb-6;
}
</style>
