<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useBot } from '../composables/useBot'

import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'
import IconShield from '../components/icons/IconShield.vue'

const router = useRouter()
const route = useRoute()

const { user, fetchUser, logout: performLogout } = useAuth()
const { botInfo, fetchBot } = useBot()

const targetUserId = route.params.id

onMounted(async () => {
  if (!user.value) await fetchUser()
  await fetchBot()
})

const handleLogout = async () => {
  await performLogout()
  router.push('/')
}

const goToAdmin = () => {
  router.push('/dashboard')
}
</script>

<template>
  <div class="relative min-h-screen bg-gray-950 flex flex-col font-sans text-white">
    <div class="absolute inset-0 pointer-events-none overflow-hidden z-0">
      <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] bg-purple-900/10 blur-[150px] rounded-full"></div>
      <div class="absolute top-[60%] -right-[10%] w-[50%] h-[50%] bg-indigo-900/10 blur-[150px] rounded-full"></div>
    </div>

    <header class="w-full max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-800/50 mb-8 z-10 relative">
      <div class="flex items-center gap-4">
        <BotBadge :botInfo="botInfo" :showSubtitle="false" />
      </div>

      <div class="flex items-center gap-4">
        <button 
          v-if="['admin', 'superadmin', 'support'].includes(user?.role || '')" 
          @click="goToAdmin" 
          class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-2 shadow-lg"
        >
          <IconShield class="w-4 h-4" />
          Админ-панель
        </button>

        <UserBadge v-if="user" :user="user" @logout="handleLogout" />
      </div>
    </header>

    <main class="w-full flex-1 flex flex-col items-center justify-center py-10 px-6 z-10 relative animate-fade-in text-center">
      
      <div class="relative w-28 h-28 flex items-center justify-center mb-8">
        <div class="absolute inset-0 bg-purple-500/20 blur-2xl rounded-full"></div>
        <div class="relative bg-gray-900/80 border border-purple-500/30 w-24 h-24 rounded-3xl flex items-center justify-center shadow-xl rotate-3">
          <svg class="w-12 h-12 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
          </svg>
        </div>
      </div>

      <h1 class="text-3xl md:text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400 mb-4">
        Профиль пользователя #{{ targetUserId }}
      </h1>
      
      <p class="text-gray-400 max-w-lg text-lg mb-10 leading-relaxed">
        Совсем скоро здесь появится ваша личная статистика, глобальный лидерборд, система достижений и многое другое!
      </p>

    </main>
  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>