<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAvatarUrl } from '../utils/helpers'
import { useToast } from '../utils/useToast'
import ConfirmModal from '../components/ConfirmModal.vue'

import IconSearch from '../components/icons/IconSearch.vue'
import IconStar from '../components/icons/IconStar.vue'
import IconChevronDown from '../components/icons/IconChevronDown.vue'

const { showToast } = useToast()

const searchQuery = ref('')
const searchResults = ref<any[]>([])
const admins = ref<any[]>([])
const API_URL = import.meta.env.VITE_API_BASE_URL

const isProcessing = ref(false)

const confirmModal = ref<{ isOpen: boolean, userId: string, username: string, currentRole: string, targetRole: string }>({
  isOpen: false, userId: '', username: '', currentRole: '', targetRole: 'admin'
})

const openConfirm = (user: any) => {
  confirmModal.value = { isOpen: true, userId: user.id, username: user.username, currentRole: user.role, targetRole: 'admin' }
}
const closeConfirm = () => { if (!isProcessing.value) confirmModal.value.isOpen = false }

const loadAdmins = async () => {
  const res = await fetch(`${API_URL}/admins/list`, { credentials: 'include' })
  if (res.ok) admins.value = (await res.json()).data
}

const search = async () => {
  if (searchQuery.value.length < 2) { searchResults.value = []; return }
  const res = await fetch(`${API_URL}/users/search?q=${searchQuery.value}`, { credentials: 'include' })
  if (res.ok) searchResults.value = (await res.json()).data
}

const executeRoleChange = async () => {
  isProcessing.value = true
  const { userId, currentRole, targetRole, username } = confirmModal.value

  const newRole = ['admin', 'support'].includes(currentRole) ? 'user' : targetRole
  
  try {
    const res = await fetch(`${API_URL}/users/role`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, role: newRole }), credentials: 'include'
    })
    
    if (res.ok) {
      showToast(`Права пользователя ${username} успешно изменены!`, 'success')
    } else {
      const err = await res.json()
      showToast(`Ошибка: ${err.detail || 'Действие отклонено'}`, 'error')
    }
  } catch (error) {
    showToast("Ошибка соединения с сервером", 'error')
  } finally {
    isProcessing.value = false
    closeConfirm()
    await loadAdmins()
    if (searchQuery.value) search()
  }
}

onMounted(loadAdmins)
</script>

<template>
  <div class="space-y-8 animate-fade-in relative">
    
    <div class="relative bg-gray-900/40 backdrop-blur-md border border-gray-800 p-8 rounded-[2rem] shadow-lg overflow-hidden">
      <div class="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 blur-[100px] rounded-full pointer-events-none"></div>

      <div class="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h2 class="text-3xl font-extrabold text-white mb-2">Управление <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">Ролями</span></h2>
          <p class="text-gray-400 font-medium">Назначайте администраторов и агентов для помощи в управлении.</p>
        </div>
        
        <div class="relative w-full md:w-[22rem]">
          <input v-model="searchQuery" @input="search" type="text" placeholder="Поиск (Ник или ID)..." 
                 class="w-full bg-gray-900/80 border border-gray-700 text-white px-5 py-3 rounded-2xl focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all placeholder-gray-500 shadow-inner">
          <IconSearch class="w-5 h-5 text-gray-400 absolute right-4 top-3.5" />
        </div>
      </div>
    </div>

    <div v-if="searchQuery.length >= 2" class="bg-gray-900/60 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-lg">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-2 h-8 bg-purple-500 rounded-full"></div>
        <h3 class="text-xl font-bold text-white">Результаты поиска</h3>
      </div>
      
      <div v-if="searchResults.length === 0" class="text-gray-500 font-medium text-center py-4 bg-gray-800/30 rounded-2xl border border-gray-700/50">Пользователи не найдены.</div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="u in searchResults" :key="'s'+u.id" class="flex items-center justify-between p-4 bg-gray-800/40 rounded-2xl border border-gray-700 hover:border-gray-600 transition-colors group">
          <div class="flex items-center gap-4">
            <img :src="getAvatarUrl(u.id, u.avatar, 64)" class="w-12 h-12 rounded-full border-2 border-gray-700 group-hover:border-purple-500/50 transition-colors object-cover">
            <div class="flex flex-col">
              <span class="font-bold text-gray-200 text-sm">{{ u.username }}</span>
              <span class="text-xs text-gray-500">ID: {{ u.id }}</span>
            </div>
          </div>
          
          <button v-if="['admin', 'support'].includes(u.role)" @click="openConfirm(u)" class="px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-sm hover:shadow-md bg-red-500/10 text-red-400 hover:bg-red-500/20">
            Забрать
          </button>
          <button v-else-if="u.role === 'user'" @click="openConfirm(u)" class="px-4 py-2 rounded-xl text-sm font-bold transition-all shadow-sm hover:shadow-md bg-purple-600 hover:bg-purple-500 text-white">
            Выдать
          </button>
          <span v-else-if="u.role === 'superadmin'" class="text-xs font-bold text-purple-400 bg-purple-500/10 px-3 py-1.5 rounded-lg border border-purple-500/20">Создатель</span>
        </div>
      </div>
    </div>

    <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 rounded-3xl p-6 shadow-lg">
      <div class="flex items-center gap-3 mb-6">
        <div class="w-2 h-8 bg-indigo-500 rounded-full"></div>
        <h3 class="text-xl font-bold text-white">Текущий персонал</h3>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div v-for="u in admins" :key="u.id" class="flex items-center justify-between p-5 bg-gray-800/40 rounded-2xl border border-gray-700/80 hover:-translate-y-1 hover:shadow-xl transition-all duration-300 group">
          <div class="flex items-center gap-4">
            <div class="relative">
              <div v-if="u.role === 'superadmin'" class="absolute inset-0 bg-purple-500 rounded-full blur-md opacity-30"></div>
              <img :src="getAvatarUrl(u.id, u.avatar, 64)" class="relative w-14 h-14 rounded-full border-2 border-gray-700 group-hover:border-indigo-500/50 transition-colors object-cover">
            </div>
            
            <div class="flex flex-col gap-1.5">
              <span class="font-bold text-gray-100">{{ u.username }}</span>
              
              <span v-if="u.role === 'superadmin'" class="bg-gradient-to-r from-pink-500 to-purple-500 text-white text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md shadow-lg flex items-center gap-1 w-max">
                <IconStar class="w-3 h-3" />
                Создатель
              </span>
              <span v-else-if="u.role === 'admin'" class="bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md w-max">
                Администратор
              </span>
              <span v-else-if="u.role === 'support'" class="bg-yellow-500/20 text-yellow-500 border border-yellow-500/30 text-[10px] uppercase tracking-wider font-bold px-2.5 py-1 rounded-md w-max flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                Агент поддержки
              </span>
            </div>
          </div>
          
          <button v-if="u.role !== 'superadmin'" @click="openConfirm(u)" class="w-10 h-10 rounded-full flex items-center justify-center bg-gray-900/50 text-gray-400 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/30 border border-transparent transition-all" title="Забрать права">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-5 h-5"><path stroke-linecap="round" stroke-linejoin="round" d="M22 10.5h-6m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM4 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 10.374 21c-2.331 0-4.512-.645-6.374-1.766Z" /></svg>
          </button>
        </div>
      </div>
    </div>

    <ConfirmModal 
      :isOpen="confirmModal.isOpen"
      :isProcessing="isProcessing"
      :type="['admin', 'support'].includes(confirmModal.currentRole) ? 'danger' : 'primary'"
      @confirm="executeRoleChange"
      @cancel="closeConfirm"
    >
      <div v-if="['admin', 'support'].includes(confirmModal.currentRole)">
        Вы уверены, что хотите <strong class="text-red-400">ЗАБРАТЬ</strong> права у пользователя <span class="text-purple-400 font-bold">{{ confirmModal.username }}</span>?
      </div>
      
      <div v-else class="flex flex-col gap-4 text-left">
        <div class="text-center text-lg">
          Вы собираетесь <strong class="text-purple-400">ВЫДАТЬ ПРАВА</strong> пользователю <span class="font-bold">{{ confirmModal.username }}</span>.
        </div>
        <div class="mt-2">
          <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Выберите уровень доступа</label>
          <div class="relative">
            <select v-model="confirmModal.targetRole" class="w-full bg-gray-900 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all outline-none appearance-none cursor-pointer">
              <option value="admin">Администратор (Полный доступ к панели)</option>
              <option value="support">Агент поддержки (Доступ только к обращениям)</option>
            </select>
            <IconChevronDown class="w-5 h-5 text-gray-400 absolute right-4 top-3.5 pointer-events-none" />
          </div>
        </div>
      </div>
    </ConfirmModal>
    
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>