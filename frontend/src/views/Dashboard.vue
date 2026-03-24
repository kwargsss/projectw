<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('Загрузка...')
const stats = ref<any>(null)

const API_URL = import.meta.env.VITE_API_BASE_URL

const logout = async () => {
  try {
    // [ПРОДАКШЕН]: credentials: 'include' ОБЯЗАТЕЛЕН, чтобы передать куку для удаления
    await fetch(`${API_URL}/auth/logout`, { 
        method: 'POST', 
        credentials: 'include' 
    })
  } catch (e) {
    console.error("Ошибка при выходе", e)
  }
  router.push('/login')
}

onMounted(async () => {
  try {
    const userRes = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })

    if (!userRes.ok) throw new Error("Не авторизован")
    
    const userData = await userRes.json()
    username.value = userData.username

    const statsRes = await fetch(`${API_URL}/stats`, { credentials: 'include' })
    if (statsRes.ok) {
      const result = await statsRes.json()
      stats.value = result.data
    }
  } catch (err) {
    router.push('/login')
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100 p-8">
    <header class="flex justify-between items-center pb-6 border-b border-gray-800 mb-10">
      <h1 class="text-3xl font-extrabold text-white">Bot<span class="text-purple-500">Panel</span></h1>
      <div class="flex items-center gap-4">
        <p>Привет, <span class="text-purple-400 font-bold">{{ username }}</span></p>
        <button @click="logout" class="bg-gray-800 hover:bg-gray-700 text-white px-4 py-2 rounded-xl border border-gray-700 transition-colors text-sm">Выйти</button>
      </div>
    </header>
    
    <div class="bg-gray-900 p-8 rounded-3xl border border-gray-800 shadow-2xl">
        <p v-if="stats" class="text-2xl font-bold">Сервер: {{ stats.name }} | Участников: {{ stats.member_count }}</p>
        <p v-else class="text-gray-500">Загрузка статистики...</p>
    </div>
  </div>
</template>