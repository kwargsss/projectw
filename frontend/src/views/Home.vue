<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Подключаем наши модули
import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'

const route = useRoute()
const router = useRouter()

const error = ref<string | null>(null)
const isLoggedIn = ref(false)

const user = ref<{id: string, username: string, avatar: string | null, role: string} | null>(null)
const botInfo = ref<{id: string | null, username: string, avatar: string | null}>({
  id: null,
  username: 'Загрузка...',
  avatar: null
})

const API_URL = import.meta.env.VITE_API_BASE_URL

onMounted(async () => {
  if (route.query.error) {
    error.value = "Ошибка авторизации. Попробуйте еще раз."
  }

  try {
    const botRes = await fetch(`${API_URL}/bot`)
    if (botRes.ok) botInfo.value = (await botRes.json()).data
  } catch (e) {}

  try {
    const res = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
    if (res.ok) {
      user.value = await res.json()
      isLoggedIn.value = true
    }
  } catch (err) {}
})

const login = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/login`)
    const data = await response.json()
    if (data.url) window.location.href = data.url
  } catch (err) {
    error.value = "Сервер недоступен."
  }
}

const logout = async () => {
  await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
  isLoggedIn.value = false
  user.value = null
}
</script>

<template>
  <div class="relative min-h-screen bg-gray-950 flex flex-col font-sans text-white overflow-hidden">
    
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
      <div class="absolute -top-[30%] -left-[10%] w-[70%] h-[70%] bg-purple-900/20 blur-[150px] rounded-full"></div>
      <div class="absolute top-[40%] -right-[20%] w-[60%] h-[60%] bg-indigo-900/20 blur-[150px] rounded-full"></div>
    </div>

    <header class="relative z-50 w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
      <BotBadge :botInfo="botInfo" :showSubtitle="false" />
      <UserBadge v-if="isLoggedIn && user" :user="user" @logout="logout" />
    </header>

    <main class="relative z-10 flex-1 flex flex-col items-center justify-center text-center px-4 pb-20">
      <div class="max-w-4xl mx-auto">
        <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-900/30 border border-purple-500/30 text-purple-300 text-sm font-bold mb-8 backdrop-blur-md shadow-[0_0_15px_rgba(168,85,247,0.15)]">
          <span class="relative flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
          </span>
          Официальная панель управления
        </div>

        <h1 class="text-5xl md:text-7xl font-extrabold mb-6 leading-tight tracking-tight text-white drop-shadow-lg">
          Управляй своим Discord <br class="hidden md:block"/>
          <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">на новом уровне</span>
        </h1>
        
        <p class="text-gray-400 text-lg md:text-xl mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
          Настраивай модули, просматривай подробную статистику и управляй экономикой сервера прямо из браузера в один клик. 
        </p>

        <div v-if="error" class="mb-8 text-red-400 bg-red-900/30 p-4 rounded-xl text-sm border border-red-800 max-w-md mx-auto backdrop-blur-sm font-semibold">
          {{ error }}
        </div>

        <div class="flex flex-col sm:flex-row items-center justify-center gap-5">
          <button v-if="!isLoggedIn" @click="login" class="group relative flex items-center justify-center gap-3 bg-purple-600 hover:bg-purple-500 text-white px-10 py-4 rounded-2xl font-extrabold text-lg transition-all duration-300 shadow-[0_0_20px_rgba(147,51,234,0.4)] hover:shadow-[0_0_40px_rgba(168,85,247,0.6)] hover:-translate-y-1 w-full sm:w-auto overflow-hidden">
            <svg class="w-6 h-6 fill-white relative z-10" viewBox="0 0 640 512" xmlns="http://www.w3.org/2000/svg"><path d="M524.531 69.836a1.5 1.5 0 0 0-.764-.7A485.065 485.065 0 0 0 404.081 32.03a1.816 1.816 0 0 0-1.923.91 337.461 337.461 0 0 0-14.9 30.6 447.848 447.848 0 0 0-134.426 0 309.541 309.541 0 0 0-15.135-30.6 1.89 1.89 0 0 0-1.924-.91 483.689 483.689 0 0 0-119.688 37.107 1.712 1.712 0 0 0-.788.676C39.068 183.651 18.186 294.69 28.43 404.354a2.016 2.016 0 0 0 .765 1.375 487.666 487.666 0 0 0 146.825 74.189 1.9 1.9 0 0 0 2.063-.676A348.2 348.2 0 0 0 208.12 430.4a1.86 1.86 0 0 0-1.019-2.588 321.173 321.173 0 0 1-45.868-21.853 1.885 1.885 0 0 1-.185-3.126 245.576 245.576 0 0 0 9.109-7.137 1.819 1.819 0 0 1 1.9-.256c96.229 43.917 200.41 43.917 295.5 0a1.812 1.812 0 0 1 1.924.233 234.533 234.533 0 0 0 9.132 7.16 1.884 1.884 0 0 1-.162 3.126 301.407 301.407 0 0 1-45.89 21.83 1.875 1.875 0 0 0-1.011 2.61 381.19 381.19 0 0 0 29.89 49.362 1.916 1.916 0 0 0 2.107.7 486.582 486.582 0 0 0 146.97-74.204 1.871 1.871 0 0 0 .774-1.351c12.198-121.152-19.177-231.066-82.903-334.331zM222.791 337.58c-28.972 0-52.844-26.587-52.844-59.239s23.409-59.241 52.844-59.241c29.665 0 53.306 26.589 52.843 59.241.013 32.654-23.41 59.239-52.843 59.239zm195.38 0c-28.971 0-52.843-26.587-52.843-59.239s23.409-59.241 52.843-59.241c29.667 0 53.307 26.589 52.844 59.241s-23.177 59.239-52.844 59.239z"/></svg>
                    <span class="relative z-10">Авторизация</span>
                    <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>

                  <button v-else @click="router.push('/dashboard')" class="group relative flex items-center justify-center gap-3 bg-white text-gray-900 hover:bg-gray-100 px-10 py-4 rounded-2xl font-extrabold text-lg transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_35px_rgba(255,255,255,0.3)] hover:-translate-y-1 w-full sm:w-auto">
                    Панель управления
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="3" stroke="currentColor" class="w-5 h-5 group-hover:translate-x-1.5 transition-transform"><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" /></svg>
                  </button>
                </div>
              </div>
            </main>
          </div>
        </template>
        ```