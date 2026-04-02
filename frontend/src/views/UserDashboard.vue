<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { useBot } from '../composables/useBot'
import { useToast } from '../utils/useToast'
import { Cropper } from 'vue-advanced-cropper'

import 'vue-advanced-cropper/dist/style.css'

import BotBadge from '../components/BotBadge.vue'
import UserBadge from '../components/UserBadge.vue'
import IconShield from '../components/icons/IconShield.vue'
import IconPhotograph from '../components/icons/IconPhotograph.vue'
import IconTrash from '../components/icons/IconTrash.vue'
import ConfirmModal from '../components/ConfirmModal.vue'

const router = useRouter()
const route = useRoute()

const { user, fetchUser, logout: performLogout } = useAuth()
const { botInfo, fetchBot } = useBot()
const { showToast } = useToast()

const targetUserId = route.params.id as string
const API_URL = import.meta.env.VITE_API_BASE_URL

const stats = ref<any>(null)
const isLoadingStats = ref(true)
let statsInterval: ReturnType<typeof setInterval> | null = null

const activeTab = ref<'xp' | 'messages' | 'voice'>('xp')
const leaderboardData = ref<any[]>([])
const isLoadingLeaderboard = ref(true)

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const isDeleting = ref(false)

const selectedImageUrl = ref<string | null>(null)
const cropperRef = ref<any>(null)

const isConfirmModalOpen = ref(false)

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  
  const file = target.files[0]
  if (file.size > 10 * 1024 * 1024) {
    showToast('Файл слишком большой! Максимальный размер 10 МБ.', 'error')
    return
  }

  selectedImageUrl.value = URL.createObjectURL(file)
  
  if (fileInput.value) fileInput.value.value = ''
}

const uploadCroppedImage = async () => {
  if (!cropperRef.value) return
  
  const { canvas } = cropperRef.value.getResult()
  if (!canvas) return

  isUploading.value = true
  
  canvas.toBlob(async (blob: Blob | null) => {
    if (!blob) {
      isUploading.value = false
      showToast('Ошибка при обработке изображения', 'error')
      return
    }

    const formData = new FormData()
    formData.append('file', blob, 'background.png')

    try {
      const res = await fetch(`${API_URL}/users/${targetUserId}/background`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      
      if (res.ok) {
        showToast('Фон успешно обновлен! Проверьте команду /ранг.', 'success')
        closeCropper()
      } else {
        showToast(data.detail || data.message || 'Ошибка загрузки фона', 'error')
      }
    } catch (err) {
      showToast('Ошибка соединения с сервером', 'error')
    } finally {
      isUploading.value = false
    }
  }, 'image/png')
}

const closeCropper = () => {
  selectedImageUrl.value = null
  isUploading.value = false
}

const deleteBackground = async () => {
  isDeleting.value = true
  try {
    const res = await fetch(`${API_URL}/users/${targetUserId}/background`, {
      method: 'DELETE'
    })
    const data = await res.json()
    
    if (res.ok) {
      showToast('Фон успешно удален!', 'success')
    } else {
      showToast(data.detail || data.message || 'Ошибка удаления фона', 'error')
    }
  } catch (err) {
    showToast('Ошибка соединения с сервером', 'error')
  } finally {
    isDeleting.value = false
    isConfirmModalOpen.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await fetch(`${API_URL}/levels/user/${targetUserId}`)
    const data = await res.json()
    if (data.status === 'ok') stats.value = data
    else stats.value = null
  } catch (err) {
    console.error('Ошибка загрузки статистики:', err)
  } finally {
    if (isLoadingStats.value) isLoadingStats.value = false
  }
}

const fetchLeaderboard = async () => {
  isLoadingLeaderboard.value = true
  try {
    const res = await fetch(`${API_URL}/levels/leaderboard?type=${activeTab.value}&target_user_id=${targetUserId}`)
    const data = await res.json()
    if (data.status === 'ok') leaderboardData.value = data.data
    else leaderboardData.value = []
  } catch (err) {
    console.error('Ошибка загрузки лидерборда:', err)
  } finally {
    isLoadingLeaderboard.value = false
  }
}

watch(activeTab, () => {
  fetchLeaderboard()
})

onMounted(async () => {
  if (!user.value) await fetchUser()
  await fetchBot()
  
  await fetchStats()
  await fetchLeaderboard()

  statsInterval = setInterval(() => {
    fetchStats()
    fetch(`${API_URL}/levels/leaderboard?type=${activeTab.value}&target_user_id=${targetUserId}`)
      .then(r => r.json())
      .then(d => { if (d.status === 'ok') leaderboardData.value = d.data })
  }, 5000)
})

onUnmounted(() => {
  if (statsInterval) clearInterval(statsInterval)
})

const xpProgress = computed(() => {
  if (!stats.value) return 0
  const level = stats.value.level
  const currentXp = stats.value.xp
  const currentLevelBaseXp = Math.pow(level, 2) * 100
  const nextLevelXp = Math.pow(level + 1, 2) * 100
  const xpNeededForLevel = nextLevelXp - currentLevelBaseXp
  const xpGainedInLevel = currentXp - currentLevelBaseXp
  let percentage = (xpGainedInLevel / xpNeededForLevel) * 100
  return Math.min(Math.max(percentage, 0), 100)
})

const nextLevelTotalXp = computed(() => {
  if (!stats.value) return 0
  return Math.pow(stats.value.level + 1, 2) * 100
})

const formatVoiceTime = (mins: number) => {
  if (!mins) return '0 м.'
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h > 0 && m > 0) return `${h} ч. ${m} м.`
  if (h > 0) return `${h} ч.`
  return `${m} м.`
}

const getDefaultAvatar = (userId: string) => {
  const hash = Number(userId.slice(-1)) % 5 
  return `https://cdn.discordapp.com/embed/avatars/${hash}.png`
}

const targetUserInfo = computed(() => {
  if (user.value && user.value.id === targetUserId) return user.value
  return null
})

const avatarUrl = computed(() => {
  if (targetUserInfo.value && targetUserInfo.value.avatar) {
    return `https://cdn.discordapp.com/avatars/${targetUserInfo.value.id}/${targetUserInfo.value.avatar}.png`
  }
  return getDefaultAvatar(targetUserId)
})

const handleLogout = async () => {
  await performLogout()
  router.push('/')
}
const goToAdmin = () => router.push('/dashboard')
</script>

<template>
  <div class="relative min-h-screen bg-gray-950 flex flex-col font-sans text-white overflow-x-hidden">
    <div class="fixed inset-0 pointer-events-none z-0">
      <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] bg-purple-900/10 blur-[150px] rounded-full"></div>
      <div class="absolute top-[60%] -right-[10%] w-[50%] h-[50%] bg-indigo-900/10 blur-[150px] rounded-full"></div>
    </div>

    <header class="w-full max-w-7xl mx-auto px-6 py-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-gray-800/50 mb-8 z-10 relative">
      <div class="flex items-center gap-4">
        <BotBadge :botInfo="botInfo" :showSubtitle="false" />
      </div>

      <div class="flex items-center gap-4">
        <button v-if="['admin', 'superadmin', 'support'].includes(user?.role || '')" @click="goToAdmin" 
          class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-2 shadow-lg">
          <IconShield class="w-4 h-4" />
          Админ-панель
        </button>
        <UserBadge v-if="user" :user="user" @logout="handleLogout" />
      </div>
    </header>

    <main class="flex-1 w-full max-w-4xl mx-auto flex flex-col py-6 px-6 z-10 relative animate-fade-in pb-20">
      
      <div class="w-full bg-gray-900/50 border border-gray-800/80 backdrop-blur-md rounded-3xl p-8 mb-8 flex flex-col md:flex-row items-center gap-8 shadow-2xl relative overflow-hidden group">
         <div class="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full group-hover:bg-purple-500/20 transition-colors duration-700"></div>
         
         <img :src="avatarUrl" class="w-32 h-32 rounded-full border-4 border-gray-800 shadow-xl z-10 object-cover" alt="Avatar" />
         
         <div class="flex-1 text-center md:text-left z-10">
            <h1 class="text-3xl font-bold text-white mb-3 tracking-wide transition-all">
               {{ targetUserInfo ? targetUserInfo.username : `Участник #${targetUserId}` }}
            </h1>
            <div class="flex flex-wrap justify-center md:justify-start gap-3">
               <span class="px-4 py-1.5 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-lg text-sm font-semibold tracking-wide flex items-center gap-2 transition-all">
                 <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                 Ранг: #{{ stats ? stats.rank : '?' }}
               </span>
               <span class="px-4 py-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-sm font-semibold tracking-wide flex items-center gap-2 transition-all">
                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                 Уровень: {{ stats ? stats.level : 0 }}
               </span>
            </div>
         </div>

         <input type="file" ref="fileInput" class="hidden" accept="image/png, image/jpeg, image/webp" @change="handleFileSelect" />
         
         <div v-if="user?.id === targetUserId" class="flex flex-col items-center md:items-end z-10 w-full md:w-auto mt-6 md:mt-0 pt-6 md:pt-0 border-t border-gray-800/50 md:border-none">
           <div class="flex items-center gap-2 w-full md:w-auto">
             <button 
               @click="triggerFileInput" 
               class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 px-5 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(99,102,241,0.1)] w-full md:w-auto group flex-1 md:flex-none"
             >
               <IconPhotograph class="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" />
               Изменить фон
             </button>

             <button 
               @click="isConfirmModalOpen = true"
               :disabled="isDeleting"
               class="bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 p-2.5 rounded-xl transition-all shadow-[0_0_15px_rgba(239,68,68,0.1)] disabled:opacity-50 flex items-center justify-center group"
               title="Сбросить фон на стандартный"
             >
               <svg v-if="isDeleting" class="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
               <IconTrash v-else class="w-5 h-5 group-hover:scale-110 transition-transform" />
             </button>
           </div>
           
           <div class="mt-3 flex items-center gap-2 text-[11px] text-gray-400 font-medium bg-gray-900/80 px-3 py-1.5 rounded-lg border border-gray-800 shadow-sm">
             <span>800x250 px</span>
             <span class="w-1 h-1 rounded-full bg-gray-600"></span>
             <span>Авто-обрезка</span>
           </div>
         </div>
      </div>

      <div v-if="isLoadingStats" class="w-full flex justify-center py-10">
         <svg class="animate-spin h-10 w-10 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
      </div>

      <div v-else-if="!stats" class="w-full bg-gray-900/40 border border-gray-800/80 rounded-3xl p-12 text-center shadow-lg mb-10">
         <div class="w-20 h-20 mx-auto bg-gray-800/50 rounded-full flex items-center justify-center mb-5 text-gray-600"><svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg></div>
         <h3 class="text-2xl font-bold text-gray-300 mb-2">Активность не найдена</h3>
         <p class="text-gray-500 max-w-sm mx-auto">Этот пользователь еще не отправлял сообщений и не общался в голосовых каналах сервера.</p>
      </div>

      <div v-else class="w-full grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
         <div class="col-span-1 md:col-span-2 bg-gray-900/60 border border-gray-800/80 rounded-2xl p-7 shadow-lg relative overflow-hidden">
            <div class="flex justify-between items-end mb-4 relative z-10">
               <div>
                  <h3 class="text-gray-400 font-semibold text-xs uppercase tracking-widest mb-1.5">Прогресс до следующего уровня</h3>
                  <div class="text-3xl font-extrabold text-white transition-all">{{ stats.xp }} <span class="text-gray-600 text-xl font-medium">/ {{ nextLevelTotalXp }} XP</span></div>
               </div>
               <div class="text-indigo-400 font-black text-xl bg-indigo-500/10 px-3 py-1 rounded-lg border border-indigo-500/20 transition-all">{{ stats.level }} <span class="text-gray-500 mx-1">➔</span> {{ stats.level + 1 }}</div>
            </div>
            <div class="w-full h-4 bg-gray-950 rounded-full overflow-hidden shadow-inner border border-gray-800/50 relative z-10">
               <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out relative" :style="`width: ${xpProgress}%`"><div class="absolute inset-0 bg-white/20 w-full h-full animate-pulse"></div></div>
            </div>
         </div>
         <div class="bg-gray-900/60 border border-gray-800/80 rounded-2xl p-6 shadow-lg flex items-center gap-6 hover:bg-gray-800/50 transition-colors group">
            <div class="w-16 h-16 bg-blue-500/10 text-blue-400 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(59,130,246,0.1)] border border-blue-500/20 group-hover:scale-105 transition-transform">
               <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
            </div>
            <div>
               <h3 class="text-gray-500 font-semibold text-xs uppercase tracking-widest mb-1">Сообщений</h3>
               <div class="text-3xl font-extrabold text-white transition-all">{{ stats.messages }}</div>
            </div>
         </div>
         <div class="bg-gray-900/60 border border-gray-800/80 rounded-2xl p-6 shadow-lg flex items-center gap-6 hover:bg-gray-800/50 transition-colors group">
            <div class="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.1)] border border-emerald-500/20 group-hover:scale-105 transition-transform">
               <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
            </div>
            <div>
               <h3 class="text-gray-500 font-semibold text-xs uppercase tracking-widest mb-1">Время в войсе</h3>
               <div class="text-3xl font-extrabold text-white transition-all">{{ formatVoiceTime(stats.voice_mins) }}</div>
            </div>
         </div>
      </div>

      <div class="w-full flex flex-col z-10 animate-fade-in-delayed">
        
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
          <h2 class="text-2xl font-bold text-white flex items-center gap-3">
            <span class="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-xl text-yellow-400 shadow-[0_0_15px_rgba(234,179,8,0.15)]">
               <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8l-3.354-1.935a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clip-rule="evenodd"></path></svg>
            </span>
            Топ сервера
          </h2>

          <div class="flex bg-gray-900/60 p-1 rounded-xl border border-gray-800 shadow-lg">
            <button @click="activeTab = 'xp'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2', activeTab === 'xp' ? 'bg-indigo-500 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50']">
              Уровень
            </button>
            <button @click="activeTab = 'messages'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2', activeTab === 'messages' ? 'bg-blue-500 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50']">
              Сообщения
            </button>
            <button @click="activeTab = 'voice'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2', activeTab === 'voice' ? 'bg-emerald-500 text-white shadow-md' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50']">
              Голос
            </button>
          </div>
        </div>

        <div class="bg-gray-900/60 border border-gray-800/80 rounded-3xl p-6 shadow-lg min-h-[300px] relative overflow-hidden">
          <div v-if="isLoadingLeaderboard" class="absolute inset-0 flex items-center justify-center bg-gray-950/50 z-20 backdrop-blur-sm">
             <svg class="animate-spin h-8 w-8 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          </div>

          <div v-if="leaderboardData.length === 0 && !isLoadingLeaderboard" class="flex flex-col items-center justify-center py-16 opacity-50">
            <IconShield class="w-12 h-12 mb-4" />
            <p class="text-lg font-semibold">Список пуст</p>
          </div>

          <div v-else class="flex flex-col gap-3">
            <template v-for="(item, idx) in leaderboardData" :key="item.user_id + '_' + item.rank">
              
              <div v-if="item.is_appended" class="flex justify-center items-center py-2 text-gray-600 opacity-60">
                 <svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M12 10a2 2 0 110 4 2 2 0 010-4zm-7 0a2 2 0 110 4 2 2 0 010-4zm14 0a2 2 0 110 4 2 2 0 010-4z"></path></svg>
              </div>

              <div class="flex items-center justify-between p-4 rounded-2xl bg-gray-950/40 border transition-colors group"
                   :class="item.user_id === targetUserId ? 'border-yellow-500/50 bg-yellow-500/5' : 'border-gray-800/50 hover:bg-gray-800/50'">
                
                <div class="flex items-center gap-5">
                  <div class="w-10 h-10 flex items-center justify-center font-bold text-lg">
                     <span v-if="item.rank === 1" class="text-3xl filter drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">👑</span>
                     <span v-else-if="item.rank === 2" class="text-3xl">🥈</span>
                     <span v-else-if="item.rank === 3" class="text-3xl">🥉</span>
                     <span v-else class="text-gray-500 bg-gray-800 w-8 h-8 rounded-full flex items-center justify-center text-sm border border-gray-700">#{{ item.rank }}</span>
                  </div>
                  
                  <div class="flex items-center gap-3">
                    <img :src="item.avatar ? `https://cdn.discordapp.com/avatars/${item.user_id}/${item.avatar}.png` : getDefaultAvatar(item.user_id)" 
                         class="w-10 h-10 rounded-full border-2 border-gray-700 group-hover:border-indigo-500 transition-colors object-cover" />
                    <div>
                      <div class="font-bold text-gray-200 group-hover:text-white transition-colors" :class="{'text-yellow-400': item.user_id === targetUserId}">
                        {{ item.username }} 
                        <span v-if="item.user_id === targetUserId" class="ml-1 text-xs bg-yellow-500/20 text-yellow-500 px-1.5 py-0.5 rounded-md">(Вы)</span>
                      </div>
                      <div class="text-xs text-gray-500">ID: {{ item.user_id }}</div>
                    </div>
                  </div>
                </div>

                <div class="text-right">
                   <div v-if="activeTab === 'xp'" class="flex flex-col items-end">
                     <span class="font-black text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">Уровень {{ item.level }}</span>
                     <span class="text-xs font-semibold text-gray-500 mt-1">{{ item.score }} XP</span>
                   </div>
                   
                   <div v-if="activeTab === 'messages'" class="flex flex-col items-end">
                     <span class="font-black text-blue-400 text-xl">{{ item.score }}</span>
                     <span class="text-[10px] font-bold uppercase text-gray-500">сообщ.</span>
                   </div>

                   <div v-if="activeTab === 'voice'" class="flex flex-col items-end">
                     <span class="font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded border border-emerald-500/20">{{ formatVoiceTime(item.score) }}</span>
                   </div>
                </div>

              </div>
            </template>
          </div>
        </div>
      </div>
    </main>

    <div v-if="selectedImageUrl" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md px-4 animate-fade-in">
      <div class="bg-gray-900 border border-gray-800 rounded-3xl p-6 w-full max-w-4xl shadow-2xl flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-white flex items-center gap-2">
            <IconPhotograph class="w-6 h-6 text-indigo-400" />
            Кадрирование фона
          </h3>
          <button @click="closeCropper" class="text-gray-500 hover:text-white transition-colors bg-gray-800 hover:bg-gray-700 rounded-full p-2">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
          </button>
        </div>
        
        <p class="text-sm text-gray-400 mb-4">
          Выделите область, которая будет отображаться в вашей карточке <span class="bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono">/ранг</span>. Пропорции зафиксированы.
        </p>

        <div class="w-full bg-black rounded-xl overflow-hidden shadow-inner border border-gray-800" style="height: 400px;">
          <Cropper
            ref="cropperRef"
            class="w-full h-full"
            :src="selectedImageUrl"
            :stencil-props="{ aspectRatio: 800 / 250 }"
            background-class="bg-black"
          />
        </div>
        
        <div class="flex justify-end gap-3 mt-6">
          <button @click="closeCropper" :disabled="isUploading" class="px-5 py-2.5 rounded-xl font-bold text-gray-400 hover:bg-gray-800 transition-colors disabled:opacity-50">
            Отмена
          </button>
          <button @click="uploadCroppedImage" :disabled="isUploading" class="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-bold transition-colors shadow-lg shadow-indigo-500/20 disabled:opacity-50">
            <svg v-if="isUploading" class="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
            <span>Обрезать и Сохранить</span>
          </button>
        </div>
      </div>
    </div>

    <ConfirmModal 
      :isOpen="isConfirmModalOpen"
      :isProcessing="isDeleting"
      type="danger"
      title="Удаление фона"
      confirmText="Да, удалить"
      cancelText="Отмена"
      @confirm="deleteBackground"
      @cancel="isConfirmModalOpen = false"
    >
      Вы уверены, что хотите удалить свой пользовательский фон? 
      Карточка в команде <b>/ранг</b> снова станет стандартного серого цвета.
    </ConfirmModal>

  </div>
</template>

<style scoped>
.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
.animate-fade-in-delayed {
  animation: fadeIn 0.4s ease-out forwards;
  animation-delay: 0.15s;
  opacity: 0;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
:deep(.vue-advanced-cropper__stencil) {
  border: 2px solid #818cf8 !important;
}
</style>