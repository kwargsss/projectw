<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useBot } from '../composables/useBot'

import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'
import IconDiscord from '../components/icons/IconDiscord.vue'
import IconArrowRight from '../components/icons/IconArrowRight.vue'

const route = useRoute()
const router = useRouter()

const { user, isLoggedIn, error, fetchUser, login, logout } = useAuth()
const { botInfo, fetchBot } = useBot()

onMounted(async () => {
  if (route.query.error) {
    error.value = "Ошибка авторизации. Попробуйте еще раз."
  }
  
  await fetchBot()
  await fetchUser()
})
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
            <IconDiscord class="w-6 h-6 fill-white relative z-10" />
            <span class="relative z-10">Авторизация</span>
            <div class="absolute inset-0 bg-gradient-to-r from-purple-400 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </button>

          <button v-else @click="router.push('/dashboard')" class="group relative flex items-center justify-center gap-3 bg-white text-gray-900 hover:bg-gray-100 px-10 py-4 rounded-2xl font-extrabold text-lg transition-all duration-300 shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_35px_rgba(255,255,255,0.3)] hover:-translate-y-1 w-full sm:w-auto">
            Панель управления
            <IconArrowRight class="w-5 h-5 group-hover:translate-x-1.5 transition-transform" />
          </button>
        </div>
      </div>
    </main>
  </div>
</template>