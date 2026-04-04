<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import IconShield from '../../components/icons/IconShield.vue'

const props = defineProps<{ stats: any, isLoadingStats: boolean, targetUserId: string }>()
const API_URL = import.meta.env.VITE_API_BASE_URL

const activeTab = ref<'xp' | 'messages' | 'voice'>('xp')
const leaderboardData = ref<any[]>([])
const isLoadingLeaderboard = ref(true)
let lbInterval: ReturnType<typeof setInterval> | null = null

const fetchLeaderboard = async () => {
  isLoadingLeaderboard.value = true
  try {
    const res = await fetch(`${API_URL}/levels/leaderboard?type=${activeTab.value}&target_user_id=${props.targetUserId}`)
    const data = await res.json()
    if (data.status === 'ok') leaderboardData.value = data.data
  } catch (err) { console.error(err) } 
  finally { isLoadingLeaderboard.value = false }
}

watch(activeTab, fetchLeaderboard)

onMounted(() => {
  fetchLeaderboard()
  lbInterval = setInterval(() => {
    fetch(`${API_URL}/levels/leaderboard?type=${activeTab.value}&target_user_id=${props.targetUserId}`)
      .then(r => r.json()).then(d => { if (d.status === 'ok') leaderboardData.value = d.data })
  }, 5000)
})
onUnmounted(() => { if (lbInterval) clearInterval(lbInterval) })

const xpProgress = computed(() => {
  if (!props.stats) return 0
  const l = props.stats.level; const xp = props.stats.xp
  const base = Math.pow(l, 2) * 100; const next = Math.pow(l + 1, 2) * 100
  return Math.min(Math.max(((xp - base) / (next - base)) * 100, 0), 100)
})
const nextLevelTotalXp = computed(() => props.stats ? Math.pow(props.stats.level + 1, 2) * 100 : 0)
const formatVoiceTime = (mins: number) => {
  if (!mins) return '0 м.'
  const h = Math.floor(mins / 60); const m = mins % 60
  return h > 0 ? (m > 0 ? `${h} ч. ${m} м.` : `${h} ч.`) : `${m} м.`
}
const getDefaultAvatar = (id: string) => `https://cdn.discordapp.com/embed/avatars/${Number(id.slice(-1)) % 5}.png`
</script>

<template>
  <div class="w-full flex flex-col z-10 animate-fade-in">
    <div v-if="isLoadingStats" class="w-full flex justify-center py-10">
       <svg class="animate-spin h-10 w-10 text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
    </div>
    <div v-else-if="!stats" class="w-full bg-gray-900/40 border border-gray-800/80 rounded-3xl p-12 text-center mb-10">
       <div class="w-20 h-20 mx-auto bg-gray-800/50 rounded-full flex items-center justify-center mb-5 text-gray-600"><svg class="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path></svg></div>
       <h3 class="text-2xl font-bold text-gray-300 mb-2">Активность не найдена</h3>
       <p class="text-gray-500 max-w-sm mx-auto">Этот пользователь еще не общался на сервере.</p>
    </div>
    <div v-else class="w-full grid grid-cols-1 md:grid-cols-2 gap-6 mb-16">
       <div class="col-span-1 md:col-span-2 bg-gray-900/60 border border-gray-800/80 rounded-2xl p-7 shadow-lg relative overflow-hidden">
          <div class="flex justify-between items-end mb-4 relative z-10">
             <div>
                <h3 class="text-gray-400 font-semibold text-xs uppercase tracking-widest mb-1.5">Прогресс до следующего уровня</h3>
                <div class="text-3xl font-extrabold text-white">{{ stats.xp }} <span class="text-gray-600 text-xl font-medium">/ {{ nextLevelTotalXp }} XP</span></div>
             </div>
             <div class="text-indigo-400 font-black text-xl bg-indigo-500/10 px-3 py-1 rounded-lg border border-indigo-500/20">{{ stats.level }} <span class="text-gray-500 mx-1">➔</span> {{ stats.level + 1 }}</div>
          </div>
          <div class="w-full h-4 bg-gray-950 rounded-full border border-gray-800/50 relative z-10">
             <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out relative" :style="`width: ${xpProgress}%`"></div>
          </div>
       </div>
       <div class="bg-gray-900/60 border border-gray-800/80 rounded-2xl p-6 shadow-lg flex items-center gap-6 hover:bg-gray-800/50 transition-colors">
          <div class="w-16 h-16 bg-blue-500/10 text-blue-400 rounded-2xl flex items-center justify-center border border-blue-500/20">
             <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
          </div>
          <div>
             <h3 class="text-gray-500 font-semibold text-xs uppercase mb-1">Сообщений</h3>
             <div class="text-3xl font-extrabold text-white">{{ stats.messages }}</div>
          </div>
       </div>
       <div class="bg-gray-900/60 border border-gray-800/80 rounded-2xl p-6 shadow-lg flex items-center gap-6 hover:bg-gray-800/50 transition-colors">
          <div class="w-16 h-16 bg-emerald-500/10 text-emerald-400 rounded-2xl flex items-center justify-center border border-emerald-500/20">
             <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
          </div>
          <div>
             <h3 class="text-gray-500 font-semibold text-xs uppercase mb-1">Время в войсе</h3>
             <div class="text-3xl font-extrabold text-white">{{ formatVoiceTime(stats.voice_mins) }}</div>
          </div>
       </div>
    </div>

    <div class="flex flex-col sm:flex-row justify-between mb-6 gap-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-3">
        <span class="p-2 bg-yellow-500/10 border border-yellow-500/20 rounded-xl text-yellow-400">
           <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zM12 2a1 1 0 01.967.744L14.146 7.2 17.5 9.134a1 1 0 010 1.732l-3.354 1.935-1.18 4.455a1 1 0 01-1.933 0L9.854 12.8l-3.354-1.935a1 1 0 010-1.732l3.354-1.935 1.18-4.455A1 1 0 0112 2z" clip-rule="evenodd"></path></svg>
        </span>
        Топ сервера
      </h2>
      <div class="flex bg-gray-900/60 p-1 rounded-xl border border-gray-800 shadow-lg">
        <button @click="activeTab = 'xp'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors', activeTab === 'xp' ? 'bg-indigo-500 text-white' : 'text-gray-400 hover:text-gray-200']">Уровень</button>
        <button @click="activeTab = 'messages'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors', activeTab === 'messages' ? 'bg-blue-500 text-white' : 'text-gray-400 hover:text-gray-200']">Сообщения</button>
        <button @click="activeTab = 'voice'" :class="['px-4 py-2 rounded-lg text-sm font-semibold transition-colors', activeTab === 'voice' ? 'bg-emerald-500 text-white' : 'text-gray-400 hover:text-gray-200']">Голос</button>
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
        <template v-for="item in leaderboardData" :key="item.user_id + '_' + item.rank">
          <div v-if="item.is_appended" class="flex justify-center items-center py-2 text-gray-600 opacity-60"><svg class="w-8 h-8" fill="currentColor" viewBox="0 0 24 24"><path d="M12 10a2 2 0 110 4 2 2 0 010-4zm-7 0a2 2 0 110 4 2 2 0 010-4zm14 0a2 2 0 110 4 2 2 0 010-4z"></path></svg></div>
          <div class="flex items-center justify-between p-4 rounded-2xl bg-gray-950/40 border transition-colors group" :class="item.user_id === targetUserId ? 'border-yellow-500/50 bg-yellow-500/5' : 'border-gray-800/50 hover:bg-gray-800/50'">
            <div class="flex items-center gap-5">
              <div class="w-10 h-10 flex items-center justify-center font-bold text-lg">
                 <span v-if="item.rank === 1" class="text-3xl filter drop-shadow-[0_0_10px_rgba(250,204,21,0.5)]">👑</span>
                 <span v-else-if="item.rank === 2" class="text-3xl">🥈</span>
                 <span v-else-if="item.rank === 3" class="text-3xl">🥉</span>
                 <span v-else class="text-gray-500 bg-gray-800 w-8 h-8 rounded-full flex items-center justify-center text-sm border border-gray-700">#{{ item.rank }}</span>
              </div>
              <div class="flex items-center gap-3">
                <img :src="item.avatar ? `https://cdn.discordapp.com/avatars/${item.user_id}/${item.avatar}.png` : getDefaultAvatar(item.user_id)" class="w-10 h-10 rounded-full border-2 border-gray-700 group-hover:border-indigo-500 transition-colors object-cover" />
                <div>
                  <div class="font-bold text-gray-200 group-hover:text-white transition-colors" :class="{'text-yellow-400': item.user_id === targetUserId}">{{ item.username }} <span v-if="item.user_id === targetUserId" class="ml-1 text-xs bg-yellow-500/20 text-yellow-500 px-1.5 py-0.5 rounded-md">(Вы)</span></div>
                  <div class="text-xs text-gray-500">ID: {{ item.user_id }}</div>
                </div>
              </div>
            </div>
            <div class="text-right">
               <div v-if="activeTab === 'xp'" class="flex flex-col items-end"><span class="font-black text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">Уровень {{ item.level }}</span><span class="text-xs font-semibold text-gray-500 mt-1">{{ item.score }} XP</span></div>
               <div v-if="activeTab === 'messages'" class="flex flex-col items-end"><span class="font-black text-blue-400 text-xl">{{ item.score }}</span><span class="text-[10px] font-bold uppercase text-gray-500">сообщ.</span></div>
               <div v-if="activeTab === 'voice'" class="flex flex-col items-end"><span class="font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded border border-emerald-500/20">{{ formatVoiceTime(item.score) }}</span></div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>