<script setup lang="ts">
import { ref, onMounted, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'

import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'
import BotStatus from '../components/BotStatus.vue'
import UserDashboard from './UserDashboard.vue'

const router = useRouter()
const route = useRoute()

const isLoading = ref(true)
const user = ref<{id: string, username: string, avatar: string | null, role: string} | null>(null)
const botInfo = ref<{id: string | null, username: string, avatar: string | null}>({ id: null, username: 'Загрузка...', avatar: null })
const stats = ref<any>(null)
const botStatus = ref<'connecting' | 'online' | 'offline'>('connecting')
const isSidebarOpen = ref(false)

provide('user', user)
provide('botInfo', botInfo)
provide('botStatus', botStatus)
provide('stats', stats)

const API_URL = import.meta.env.VITE_API_BASE_URL

const handleStatsUpdate = (newStats: any) => {
  stats.value = newStats
  botStatus.value = newStats ? 'online' : 'offline'
  isLoading.value = false 
}

onMounted(async () => {
  try {
    const userRes = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
    if (!userRes.ok) throw new Error("Не авторизован")
    user.value = await userRes.json()

    try {
      const botRes = await fetch(`${API_URL}/bot`)
      if (botRes.ok) botInfo.value = (await botRes.json()).data
    } catch (e) {}
  } catch (err) { router.push('/') }
})

const logout = async () => {
  await fetch(`${API_URL}/auth/logout`, { method: 'POST', credentials: 'include' })
  router.push('/')
}
</script>

<template>
  <div class="relative min-h-screen bg-gray-950 flex flex-col font-sans text-white">
    <div class="absolute inset-0 pointer-events-none overflow-hidden z-0">
      <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] bg-purple-900/10 blur-[150px] rounded-full"></div>
      <div class="absolute top-[60%] -right-[10%] w-[50%] h-[50%] bg-indigo-900/10 blur-[150px] rounded-full"></div>
    </div>

    <div v-if="isLoading && !user" class="flex flex-col items-center justify-center min-h-screen z-10 relative">
      <div class="w-12 h-12 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mb-4"></div>
    </div>

    <template v-else>
      <div class="flex-1 flex flex-col transition-all duration-300 z-10" :class="isSidebarOpen && user?.role !== 'user' ? 'ml-64' : 'ml-0'">
        
        <header class="w-full max-w-7xl mx-auto px-6 py-6 flex justify-between items-center border-b border-gray-800/50 mb-8 transition-all">
          
          <div class="flex items-center gap-4">
            <button v-if="user?.role !== 'user'" @click="isSidebarOpen = !isSidebarOpen" class="w-12 h-12 rounded-full bg-gray-900/80 border border-gray-700 flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg">
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M12 17.25h8.25" /></svg>
            </button>
            <BotBadge :botInfo="botInfo" :showSubtitle="user?.role !== 'user'" />
          </div>

          <div class="flex items-center gap-4">
            <BotStatus v-if="user?.role !== 'user'" @updateStats="handleStatsUpdate" />
            <UserBadge v-if="user" :user="user" @logout="logout" />
          </div>
        </header>

        <main class="w-full max-w-7xl mx-auto px-6 pb-20 flex-1 relative z-10">
          <UserDashboard v-if="user?.role === 'user'" :user="user" />
          <template v-else>
            
            <div v-if="route.path === '/dashboard'" class="mb-10">
              <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-2">Добро пожаловать, <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">{{ user?.username }}</span>!</h1>
              <p class="text-gray-400 font-medium">Система управления сервером.</p>
            </div>
            
            <router-view></router-view>
          </template>
        </main>
      </div>

      <aside v-if="user?.role !== 'user'" class="fixed left-0 top-0 h-full w-64 bg-gray-900/95 backdrop-blur-xl border-r border-gray-800 rounded-r-[2rem] transition-transform duration-300 z-50 flex flex-col shadow-[20px_0_50px_rgba(0,0,0,0.5)]"
             :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center">
          <h2 class="font-bold text-gray-200">Навигация</h2>
          <button @click="isSidebarOpen = false" class="text-gray-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" /></svg>
          </button>
        </div>
        
        <nav class="flex-1 p-4 flex flex-col gap-2 mt-4">
          <router-link to="/dashboard" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard' ? 'bg-purple-600/20 text-purple-400 border-purple-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
            Статистика
          </router-link>

          <router-link v-if="user?.role === 'superadmin'" to="/dashboard/admins" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard/admins' ? 'bg-purple-600/20 text-purple-400 border-purple-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" /></svg>
            Администраторы
          </router-link>

          <router-link to="/dashboard/embed" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard/embed' ? 'bg-purple-600/20 text-purple-400 border-purple-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 0 1-2.25 2.25M16.5 7.5V18a2.25 2.25 0 0 0 2.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 0 0 2.25 2.25h13.5M6 7.5h3v3H6v-3Z" /></svg>
            Отправка Embed
          </router-link>  

        </nav>
      </aside>

      <div v-if="isSidebarOpen && user?.role !== 'user'" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/50 z-40 lg:hidden"></div>
    </template>
  </div>
</template>