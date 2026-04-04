<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
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
import IconMenu from '../components/icons/IconMenu.vue'
import IconChevronLeft from '../components/icons/IconChevronLeft.vue'
import ConfirmModal from '../components/ConfirmModal.vue'

const router = useRouter()
const route = useRoute()

const { user, fetchUser, logout: performLogout } = useAuth()
const { botInfo, fetchBot } = useBot()
const { showToast } = useToast()

const targetUserId = computed(() => route.params.id as string)
const API_URL = import.meta.env.VITE_API_BASE_URL

const stats = ref<any>(null)
const isLoadingStats = ref(true)
let statsInterval: ReturnType<typeof setInterval> | null = null

const isSidebarOpen = ref(false)

const fileInput = ref<HTMLInputElement | null>(null)
const isUploading = ref(false)
const isDeleting = ref(false)
const selectedImageUrl = ref<string | null>(null)
const cropperRef = ref<any>(null)
const isConfirmModalOpen = ref(false)

const triggerFileInput = () => fileInput.value?.click()

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files || target.files.length === 0) return
  const file = target.files[0]
  if (file.size > 10 * 1024 * 1024) return showToast('Файл слишком большой!', 'error')
  selectedImageUrl.value = URL.createObjectURL(file)
  if (fileInput.value) fileInput.value.value = ''
}

const uploadCroppedImage = async () => {
  if (!cropperRef.value) return
  const { canvas } = cropperRef.value.getResult()
  if (!canvas) return
  isUploading.value = true
  
  canvas.toBlob(async (blob: Blob | null) => {
    if (!blob) { isUploading.value = false; return showToast('Ошибка', 'error') }
    const formData = new FormData()
    formData.append('file', blob, 'background.png')
    try {
      const res = await fetch(`${API_URL}/users/${targetUserId.value}/background`, { method: 'POST', body: formData })
      if (res.ok) { showToast('Фон обновлен!', 'success'); closeCropper() } 
      else showToast('Ошибка загрузки', 'error')
    } catch (err) { showToast('Ошибка сервера', 'error') } 
    finally { isUploading.value = false }
  }, 'image/png')
}

const closeCropper = () => { selectedImageUrl.value = null; isUploading.value = false }

const deleteBackground = async () => {
  isDeleting.value = true
  try {
    const res = await fetch(`${API_URL}/users/${targetUserId.value}/background`, { method: 'DELETE' })
    if (res.ok) showToast('Фон удален!', 'success')
  } finally { isDeleting.value = false; isConfirmModalOpen.value = false }
}

const fetchStats = async () => {
  try {
    const res = await fetch(`${API_URL}/levels/user/${targetUserId.value}`)
    const data = await res.json()
    if (data.status === 'ok') stats.value = data
  } finally { isLoadingStats.value = false }
}

onMounted(async () => {
  if (!user.value) await fetchUser()
  await fetchBot()
  await fetchStats()
  statsInterval = setInterval(fetchStats, 5000)
})

onUnmounted(() => { if (statsInterval) clearInterval(statsInterval) })

const getDefaultAvatar = (userId: string) => `https://cdn.discordapp.com/embed/avatars/${Number(userId.slice(-1)) % 5}.png`

const targetUserInfo = computed(() => (user.value && user.value.id === targetUserId.value) ? user.value : null)
const avatarUrl = computed(() => targetUserInfo.value?.avatar ? `https://cdn.discordapp.com/avatars/${targetUserInfo.value.id}/${targetUserInfo.value.avatar}.png` : getDefaultAvatar(targetUserId.value))

const handleLogout = async () => { await performLogout(); router.push('/') }

// Автоматическое закрытие только на телефонах при клике по ссылке
const closeOnMobile = () => {
  if (window.innerWidth < 768) isSidebarOpen.value = false
}
</script>

<template>
  <div class="relative min-h-screen bg-gray-950 flex flex-col font-sans text-white overflow-x-hidden">
    <div class="fixed inset-0 pointer-events-none z-0">
      <div class="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] bg-purple-900/10 blur-[150px] rounded-full"></div>
      <div class="absolute top-[60%] -right-[10%] w-[50%] h-[50%] bg-indigo-900/10 blur-[150px] rounded-full"></div>
    </div>

    <div class="flex-1 flex flex-col transition-all duration-300 z-10" :class="isSidebarOpen ? 'md:ml-64' : 'ml-0 md:ml-20'">
      
      <header class="w-full px-6 py-4 flex justify-between items-center border-b border-gray-800/50 z-40 sticky top-0 bg-gray-950/80 backdrop-blur-md transition-all">
        <div class="flex items-center gap-4">
          <button @click="isSidebarOpen = !isSidebarOpen" class="md:hidden w-12 h-12 rounded-full bg-gray-900/80 border border-gray-700 flex items-center justify-center hover:bg-gray-800 transition-colors shadow-lg">
             <IconMenu class="w-6 h-6" />
          </button>
          <BotBadge :botInfo="botInfo" :showSubtitle="false" class="hidden sm:flex" />
        </div>

        <div class="flex items-center gap-4">
          <button v-if="['admin', 'superadmin', 'support'].includes(user?.role || '')" @click="router.push('/dashboard')" 
            class="hidden sm:flex bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 px-4 py-2 rounded-xl text-sm font-bold transition-colors items-center gap-2 shadow-lg">
            <IconShield class="w-4 h-4" />
            Админ-панель
          </button>
          <UserBadge v-if="user" :user="user" @logout="handleLogout" />
        </div>
      </header>

      <main class="w-full max-w-5xl mx-auto px-6 pt-8 pb-20 flex-1 relative z-10 animate-fade-in">
        
        <div class="w-full bg-gray-900/50 border border-gray-800/80 backdrop-blur-md rounded-3xl p-8 mb-8 flex flex-col md:flex-row items-center gap-8 shadow-2xl relative overflow-hidden group">
           <div class="absolute -right-20 -top-20 w-64 h-64 bg-indigo-500/10 blur-[80px] rounded-full group-hover:bg-purple-500/20 transition-colors duration-700"></div>
           <img :src="avatarUrl" class="w-32 h-32 rounded-full border-4 border-gray-800 shadow-xl z-10 object-cover" />
           <div class="flex-1 text-center md:text-left z-10">
              <h1 class="text-3xl font-bold text-white mb-3 tracking-wide">{{ targetUserInfo ? targetUserInfo.username : `Участник #${targetUserId}` }}</h1>
              <div class="flex flex-wrap justify-center md:justify-start gap-3">
                 <span class="px-4 py-1.5 bg-purple-500/10 border border-purple-500/20 text-purple-400 rounded-lg text-sm font-semibold tracking-wide flex items-center gap-2">
                   <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path></svg>
                   Ранг: #{{ stats ? stats.rank : '?' }}
                 </span>
                 <span class="px-4 py-1.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-sm font-semibold tracking-wide flex items-center gap-2">
                   <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                   Уровень: {{ stats ? stats.level : 0 }}
                 </span>
              </div>
           </div>
           <input type="file" ref="fileInput" class="hidden" accept="image/png, image/jpeg, image/webp" @change="handleFileSelect" />
           <div v-if="user?.id === targetUserId" class="flex flex-col items-center md:items-end z-10 w-full md:w-auto mt-6 md:mt-0 pt-6 md:pt-0 border-t border-gray-800/50 md:border-none">
             <div class="flex items-center gap-2 w-full md:w-auto">
               <button @click="triggerFileInput" class="bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 px-5 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 w-full md:w-auto group">
                 <IconPhotograph class="w-5 h-5 text-indigo-400 group-hover:scale-110 transition-transform" /> Изменить фон
               </button>
               <button @click="isConfirmModalOpen = true" :disabled="isDeleting" class="bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 p-2.5 rounded-xl transition-all disabled:opacity-50 group">
                 <IconTrash class="w-5 h-5 group-hover:scale-110 transition-transform" />
               </button>
             </div>
           </div>
        </div>

        <router-view :stats="stats" :isLoadingStats="isLoadingStats" :targetUserId="targetUserId" :key="$route.fullPath"></router-view>

      </main>
    </div>

    <aside class="fixed left-0 top-0 h-full bg-gray-900/95 backdrop-blur-xl border-r border-gray-800 rounded-r-[2rem] transition-all duration-300 z-50 flex flex-col shadow-[20px_0_50px_rgba(0,0,0,0.5)] overflow-hidden"
           :class="isSidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full md:translate-x-0 md:w-20'">
      
      <div class="p-6 border-b border-gray-800 flex items-center h-[73px]" :class="isSidebarOpen ? 'justify-between' : 'justify-center'">
        <h2 class="font-bold text-gray-200 whitespace-nowrap overflow-hidden transition-all duration-300" :class="isSidebarOpen ? 'w-auto opacity-100' : 'w-0 opacity-0 hidden'">Навигация</h2>
        <button @click="isSidebarOpen = !isSidebarOpen" class="text-gray-400 hover:text-white transition-colors flex-shrink-0">
          <IconMenu v-if="!isSidebarOpen" class="w-6 h-6 hidden md:block" />
          <IconChevronLeft v-else class="w-6 h-6" />
        </button>
      </div>

      <nav class="flex-1 p-4 flex flex-col gap-2 mt-4 overflow-y-auto overflow-x-hidden">
        <router-link :to="`/profile/${targetUserId}`" exact-active-class="bg-indigo-500/10 text-indigo-400 border-indigo-500/30" :title="!isSidebarOpen ? 'Обзор' : ''" @click="closeOnMobile" class="flex items-center rounded-xl py-3 font-semibold transition-all border group" :class="isSidebarOpen ? 'px-4 justify-start' : 'justify-center px-0 text-gray-400 hover:text-white hover:bg-gray-800/50 border-transparent'">
           <svg class="w-6 h-6 flex-shrink-0 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
           <span class="whitespace-nowrap transition-all duration-300" :class="isSidebarOpen ? 'opacity-100 ml-3 max-w-[200px]' : 'opacity-0 max-w-0 ml-0'">Обзор</span>
        </router-link>

        <router-link :to="`/profile/${targetUserId}/music`" active-class="bg-purple-500/10 text-purple-400 border-purple-500/30" :title="!isSidebarOpen ? 'Музыка' : ''" @click="closeOnMobile" class="flex items-center rounded-xl py-3 font-semibold transition-all border group" :class="isSidebarOpen ? 'px-4 justify-start' : 'justify-center px-0 text-gray-400 hover:text-white hover:bg-gray-800/50 border-transparent'">
           <svg class="w-6 h-6 flex-shrink-0 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
           <span class="whitespace-nowrap transition-all duration-300" :class="isSidebarOpen ? 'opacity-100 ml-3 max-w-[200px]' : 'opacity-0 max-w-0 ml-0'">Музыка</span>
        </router-link>
        
        <button v-if="['admin', 'superadmin', 'support'].includes(user?.role || '')" @click="router.push('/dashboard')" :title="!isSidebarOpen ? 'Админ-панель' : ''" class="mt-auto sm:hidden w-full bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 py-2.5 rounded-xl text-sm font-bold transition-all flex items-center shadow-lg mb-2" :class="isSidebarOpen ? 'px-4 justify-center gap-2' : 'justify-center px-0'">
          <IconShield class="w-6 h-6 flex-shrink-0" /> 
          <span class="whitespace-nowrap transition-all duration-300" :class="isSidebarOpen ? 'opacity-100 max-w-[200px]' : 'opacity-0 max-w-0'">Админ-панель</span>
        </button>
      </nav>
    </aside>

    <div v-if="isSidebarOpen" @click="isSidebarOpen = false" class="fixed inset-0 bg-black/50 z-40 md:hidden backdrop-blur-sm"></div>

    <div v-if="selectedImageUrl" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md px-4 animate-fade-in">
      <div class="bg-gray-900 border border-gray-800 rounded-3xl p-6 w-full max-w-4xl shadow-2xl flex flex-col">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-white flex items-center gap-2"><IconPhotograph class="w-6 h-6 text-indigo-400" /> Кадрирование фона</h3>
          <button @click="closeCropper" class="text-gray-500 hover:text-white bg-gray-800 rounded-full p-2"><svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg></button>
        </div>
        <div class="w-full bg-black rounded-xl overflow-hidden border border-gray-800" style="height: 400px;">
          <Cropper ref="cropperRef" class="w-full h-full" :src="selectedImageUrl" :stencil-props="{ aspectRatio: 800 / 250 }" background-class="bg-black" />
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="closeCropper" :disabled="isUploading" class="px-5 py-2.5 rounded-xl font-bold text-gray-400 hover:bg-gray-800 disabled:opacity-50">Отмена</button>
          <button @click="uploadCroppedImage" :disabled="isUploading" class="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-bold disabled:opacity-50">Обрезать и Сохранить</button>
        </div>
      </div>
    </div>

    <ConfirmModal :isOpen="isConfirmModalOpen" :isProcessing="isDeleting" type="danger" title="Удаление фона" confirmText="Да, удалить" cancelText="Отмена" @confirm="deleteBackground" @cancel="isConfirmModalOpen = false">
      Удалить фон и вернуть стандартный цвет в карточке /ранг?
    </ConfirmModal>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
:deep(.vue-advanced-cropper__stencil) { border: 2px solid #818cf8 !important; }
</style>