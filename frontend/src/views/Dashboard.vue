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

const dashboardMode = ref<'admin' | 'user'>('user')

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

    if (user.value && user.value.role !== 'user') {
      dashboardMode.value = 'admin'

      if (user.value.role === 'support' && route.path === '/dashboard') {
        router.push('/dashboard/tickets')
      }
    }

    try {
      const botRes = await fetch(`${API_URL}/bot`)
      if (botRes.ok) botInfo.value = (await botRes.json()).data
    } catch (e) {}
  } catch (err) { router.push('/') }
})

const toggleMode = () => {
  dashboardMode.value = dashboardMode.value === 'admin' ? 'user' : 'admin'
  isSidebarOpen.value = false
}

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
      <div class="flex-1 flex flex-col transition-all duration-300 z-10" :class="isSidebarOpen && dashboardMode === 'admin' ? 'ml-64' : 'ml-0'">
        
        <header class="w-full max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-800/50 mb-8 transition-all">
          
          <div class="flex items-center gap-4">
            <button v-if="dashboardMode === 'admin'" @click="isSidebarOpen = !isSidebarOpen" class="w-12 h-12 rounded-full bg-gray-900/80 border border-gray-700 flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg">
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M12 17.25h8.25" /></svg>
            </button>
            <BotBadge :botInfo="botInfo" :showSubtitle="dashboardMode === 'admin'" />
          </div>

          <div class="flex items-center gap-4">
            <button v-if="user && user.role !== 'user'" @click="toggleMode" class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-2 shadow-lg">
              <svg v-if="dashboardMode === 'admin'" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25" /></svg>
              {{ dashboardMode === 'admin' ? 'Людской дашборд' : 'Админ-панель' }}
            </button>

            <BotStatus v-if="dashboardMode === 'admin'" @updateStats="handleStatsUpdate" />
            <UserBadge v-if="user" :user="user" @logout="logout" />
          </div>
        </header>

        <main class="w-full max-w-7xl mx-auto px-6 pb-20 flex-1 relative z-10">
          <UserDashboard v-if="dashboardMode === 'user'" :user="user" />
          
          <template v-else>
            <div v-if="route.path === '/dashboard' && user?.role !== 'support'" class="mb-10">
              <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-2">Добро пожаловать, <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">{{ user?.username }}</span>!</h1>
              <p class="text-gray-400 font-medium">Система управления сервером.</p>
            </div>
            <router-view></router-view>
          </template>
        </main>
      </div>

      <aside v-if="dashboardMode === 'admin'" class="fixed left-0 top-0 h-full w-64 bg-gray-900/95 backdrop-blur-xl border-r border-gray-800 rounded-r-[2rem] transition-transform duration-300 z-50 flex flex-col shadow-[20px_0_50px_rgba(0,0,0,0.5)]"
             :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center">
          <h2 class="font-bold text-gray-200">Навигация</h2>
          <button @click="isSidebarOpen = false" class="text-gray-400 hover:text-white transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5 8.25 12l7.5-7.5" /></svg>
          </button>
        </div>
        
        <nav class="flex-1 p-4 flex flex-col gap-2 mt-4 overflow-y-auto">
          
          <router-link v-if="['admin', 'superadmin'].includes(user?.role || '')" to="/dashboard" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard' ? 'bg-purple-600/20 text-purple-400 border-purple-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
            Статистика
          </router-link>

          <router-link to="/dashboard/tickets" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard/tickets' ? 'bg-yellow-600/20 text-yellow-400 border-yellow-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 6v.75m0 3v.75m0 3v.75m0 3V18m-9-5.25h5.25M7.5 15h3M3.375 5.25c-.621 0-1.125.504-1.125 1.125v3.026a2.999 2.999 0 010 5.198v3.026c0 .621.504 1.125 1.125 1.125h17.25c.621 0 1.125-.504 1.125-1.125v-3.026a2.999 2.999 0 010-5.198V6.375c0-.621-.504-1.125-1.125-1.125H3.375z" /></svg>
            Обращения
          </router-link>

          <router-link v-if="['admin', 'superadmin'].includes(user?.role || '')" to="/dashboard/embed" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path.includes('/dashboard/embed') ? 'bg-purple-600/20 text-purple-400 border-purple-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 0 1-2.25 2.25M16.5 7.5V18a2.25 2.25 0 0 0 2.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 0 0 2.25 2.25h13.5M6 7.5h3v3H6v-3Z" /></svg>
            Отправка Embed
          </router-link>  

          <router-link v-if="['admin', 'superadmin'].includes(user?.role || '')" to="/dashboard/notifications" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard/notifications' ? 'bg-green-600/20 text-green-400 border-green-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg>
            Оповещения
          </router-link>

          <router-link v-if="user?.role === 'superadmin'" to="/dashboard/admins" @click="isSidebarOpen = false" 
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="$route.path === '/dashboard/admins' ? 'bg-pink-600/20 text-pink-400 border-pink-500/20' : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75m-3-7.036A11.959 11.959 0 0 1 3.598 6 11.99 11.99 0 0 0 3 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285Z" /></svg>
            Управление персоналом
          </router-link>

        </nav>
      </aside>

      <div v-if="isSidebarOpen && dashboardMode === 'admin'" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/50 z-40 lg:hidden"></div>
    </template>
  </div>
</template>