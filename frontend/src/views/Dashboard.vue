<script setup lang="ts">
import { ref, computed, onMounted, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useBot } from '../composables/useBot'

import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'
import BotStatus from '../components/BotStatus.vue'

import IconMenu from '../components/icons/IconMenu.vue'
import IconUserGroup from '../components/icons/IconUserGroup.vue'
import IconChevronLeft from '../components/icons/IconChevronLeft.vue'
import IconChartBar from '../components/icons/IconChartBar.vue'
import IconTicket from '../components/icons/IconTicket.vue'
import IconPaperAirplane from '../components/icons/IconPaperAirplane.vue'
import IconBellAlert from '../components/icons/IconBellAlert.vue'
import IconUserShield from '../components/icons/IconUserShield.vue'

const router = useRouter()
const route = useRoute()

const { user, fetchUser, logout: performLogout } = useAuth()
const { botInfo, fetchBot } = useBot()

const isLoading = ref(true)
const stats = ref<any>(null)
const botStatus = ref<'connecting' | 'online' | 'offline'>('connecting')
const isSidebarOpen = ref(false)

provide('user', user)
provide('botInfo', botInfo)
provide('botStatus', botStatus)
provide('stats', stats)

const handleStatsUpdate = (newStats: any) => {
  stats.value = newStats
  botStatus.value = newStats ? 'online' : 'offline'
  isLoading.value = false 
}

onMounted(async () => {
  await fetchUser()

  if (!user.value) {
    router.push('/')
    return
  }

  if (user.value.role === 'support' && route.path === '/dashboard') {
    router.push('/dashboard/tickets')
  }

  await fetchBot()
})

const goToUserProfile = () => {
  router.push(`/profile/${user.value?.id}`)
}

const handleLogout = async () => {
  await performLogout()
  router.push('/')
}

const sidebarLinksConfig = [
  {
    name: 'Статистика',
    path: '/dashboard',
    icon: IconChartBar,
    roles: ['admin', 'superadmin'],
    isActive: (p: string) => p === '/dashboard',
    activeClass: 'bg-purple-600/20 text-purple-400 border-purple-500/20'
  },
  {
    name: 'Обращения',
    path: '/dashboard/tickets',
    icon: IconTicket,
    roles: ['admin', 'superadmin', 'support'],
    isActive: (p: string) => p === '/dashboard/tickets',
    activeClass: 'bg-yellow-600/20 text-yellow-400 border-yellow-500/20'
  },
  {
    name: 'Отправка Embed',
    path: '/dashboard/embed',
    icon: IconPaperAirplane,
    roles: ['admin', 'superadmin'],
    isActive: (p: string) => p.includes('/dashboard/embed'),
    activeClass: 'bg-purple-600/20 text-purple-400 border-purple-500/20'
  },
  {
    name: 'Оповещения',
    path: '/dashboard/notifications',
    icon: IconBellAlert,
    roles: ['admin', 'superadmin'],
    isActive: (p: string) => p === '/dashboard/notifications',
    activeClass: 'bg-green-600/20 text-green-400 border-green-500/20'
  },
  {
    name: 'Управление персоналом',
    path: '/dashboard/admins',
    icon: IconUserShield,
    roles: ['superadmin'],
    isActive: (p: string) => p === '/dashboard/admins',
    activeClass: 'bg-pink-600/20 text-pink-400 border-pink-500/20'
  }
]

const visibleSidebarLinks = computed(() => {
  const currentRole = user.value?.role || ''
  return sidebarLinksConfig.filter(link => link.roles.includes(currentRole))
})
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
      <div class="flex-1 flex flex-col transition-all duration-300 z-10" :class="isSidebarOpen ? 'md:ml-64' : 'ml-0'">
        
        <header class="w-full max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-800/50 mb-8 transition-all">
          <div class="flex items-center gap-4">
            <button @click="isSidebarOpen = !isSidebarOpen" class="w-12 h-12 rounded-full bg-gray-900/80 border border-gray-700 flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg">
               <IconMenu class="w-6 h-6" />
            </button>
            <BotBadge :botInfo="botInfo" :showSubtitle="true" />
          </div>

          <div class="flex items-center gap-4">
            <button @click="goToUserProfile" class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-2 shadow-lg">
              <IconUserGroup class="w-4 h-4" />
              Людской дашборд
            </button>

            <BotStatus @updateStats="handleStatsUpdate" />
            <UserBadge v-if="user" :user="user" @logout="handleLogout" />
          </div>
        </header>

        <main class="w-full max-w-7xl mx-auto px-6 pb-20 flex-1 relative z-10">
          <div v-if="route.path === '/dashboard' && user?.role !== 'support'" class="mb-10">
            <h1 class="text-3xl md:text-4xl font-extrabold text-white mb-2">Добро пожаловать, <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">{{ user?.username }}</span>!</h1>
            <p class="text-gray-400 font-medium">Система управления сервером.</p>
          </div>
          <router-view></router-view>
        </main>
      </div>

      <aside class="fixed left-0 top-0 h-full w-64 bg-gray-900/95 backdrop-blur-xl border-r border-gray-800 rounded-r-[2rem] transition-transform duration-300 z-50 flex flex-col shadow-[20px_0_50px_rgba(0,0,0,0.5)]"
             :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center">
          <h2 class="font-bold text-gray-200">Навигация</h2>
          <button @click="isSidebarOpen = false" class="text-gray-400 hover:text-white transition-colors">
            <IconChevronLeft class="w-6 h-6" />
          </button>
        </div>
        
        <nav class="flex-1 p-4 flex flex-col gap-2 mt-4 overflow-y-auto">
          <router-link
            v-for="link in visibleSidebarLinks"
            :key="link.path"
            :to="link.path"
            @click="isSidebarOpen = false"
            class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors border"
            :class="link.isActive($route.path) ? link.activeClass : 'border-transparent text-gray-400 hover:bg-gray-800/80 hover:text-gray-200'"
          >
            <component :is="link.icon" class="w-5 h-5" />
            {{ link.name }}
          </router-link>
        </nav>
      </aside>

      <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/50 z-40 md:hidden"></div>
    </template>
  </div>
</template>