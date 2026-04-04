<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../../composables/useAuth'
import { useToast } from '../../utils/useToast'
import IconTrash from '../../components/icons/IconTrash.vue'
import IconSearch from '../../components/icons/IconSearch.vue'
import ConfirmModal from '../../components/ConfirmModal.vue'

const props = defineProps<{ targetUserId: string }>()
const { user } = useAuth()
const { showToast } = useToast()
const API_URL = import.meta.env.VITE_API_BASE_URL

const topTracks = ref<any[]>([])
const playlists = ref<any[]>([])
const isLoading = ref(true)

const newPlaylistName = ref('')
const trackQueries = ref<Record<string, string>>({})
const importUrls = ref<Record<string, string>>({})
const filterQueries = ref<Record<string, string>>({})

const isSearching = ref<Record<string, boolean>>({})
const isImporting = ref<Record<string, boolean>>({})

const trackToDelete = ref<{playlistName: string, index: number} | null>(null)
const isDeletingTrack = ref(false)

const playlistToDelete = ref<string | null>(null)
const isDeletingPlaylist = ref(false)

const isOwner = computed(() => user.value?.id === props.targetUserId)

const fetchData = async () => {
  isLoading.value = true
  try {
    const [topRes, plRes] = await Promise.all([
      fetch(`${API_URL}/music/top/user/${props.targetUserId}`),
      fetch(`${API_URL}/music/playlists/${props.targetUserId}`)
    ])
    
    const topData = await topRes.json()
    const plData = await plRes.json()
    
    if (topData.status === 'ok') topTracks.value = topData.data
    if (plData.status === 'ok') playlists.value = plData.data
  } catch (err) {
    console.error(err)
  } finally {
    isLoading.value = false
  }
}

const createPlaylist = async () => {
  if (!newPlaylistName.value.trim()) return
  try {
    const res = await fetch(`${API_URL}/music/playlists/${props.targetUserId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newPlaylistName.value.trim() })
    })
    const data = await res.json()
    if (data.status === 'ok') {
      showToast('Плейлист создан', 'success')
      newPlaylistName.value = ''
      fetchData()
    } else {
      showToast(data.message, 'error')
    }
  } catch (e) { showToast('Ошибка сервера', 'error') }
}

const requestDeletePlaylist = (name: string) => {
  playlistToDelete.value = name
}

const confirmDeletePlaylist = async () => {
  if (!playlistToDelete.value) return
  isDeletingPlaylist.value = true
  try {
    const res = await fetch(`${API_URL}/music/playlists/${props.targetUserId}/${playlistToDelete.value}`, { method: 'DELETE' })
    if (res.ok) {
        showToast('Плейлист удален', 'success')
        fetchData()
    }
  } catch (e) { 
    showToast('Ошибка сервера', 'error') 
  } finally { 
    isDeletingPlaylist.value = false
    playlistToDelete.value = null
  }
}

const addTrack = async (playlistName: string) => {
  const query = trackQueries.value[playlistName]
  if (!query?.trim()) return
  
  isSearching.value[playlistName] = true
  try {
    const res = await fetch(`${API_URL}/music/playlists/${props.targetUserId}/${playlistName}/tracks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query.trim() })
    })
    const data = await res.json()
    if (data.status === 'ok') {
      trackQueries.value[playlistName] = ''
      showToast('Ищем и добавляем трек...', 'success')
      setTimeout(fetchData, 3000)
    } else {
      showToast(data.message, 'error')
    }
  } catch (e) { showToast('Ошибка сервера', 'error') }
  finally { isSearching.value[playlistName] = false }
}

const importPlaylistTracks = async (playlistName: string) => {
  const url = importUrls.value[playlistName]
  if (!url?.trim()) return
  
  isImporting.value[playlistName] = true
  try {
    const res = await fetch(`${API_URL}/music/playlists/${props.targetUserId}/${playlistName}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.trim() })
    })
    const data = await res.json()
    if (data.status === 'ok') {
      importUrls.value[playlistName] = ''
      showToast('Запущен импорт плейлиста...', 'success')
      setTimeout(fetchData, 4000)
    } else {
      showToast(data.message, 'error')
    }
  } catch (e) { showToast('Ошибка сервера', 'error') }
  finally { isImporting.value[playlistName] = false }
}

const requestDeleteTrack = (playlistName: string, index: number) => {
  trackToDelete.value = { playlistName, index }
}

const confirmDeleteTrack = async () => {
  if (!trackToDelete.value) return
  isDeletingTrack.value = true
  try {
    await fetch(`${API_URL}/music/playlists/${props.targetUserId}/${trackToDelete.value.playlistName}/tracks/${trackToDelete.value.index}`, { method: 'DELETE' })
    fetchData()
  } catch (e) { 
    showToast('Ошибка сервера', 'error') 
  } finally { 
    isDeletingTrack.value = false
    trackToDelete.value = null
  }
}

const getFilteredTracks = (playlistName: string, tracks: any[]) => {
  const query = (filterQueries.value[playlistName] || '').toLowerCase().trim()
  const mapped = tracks.map((t, idx) => ({ ...t, originalIndex: idx }))
  if (!query) return mapped
  return mapped.filter(t => 
    t.title.toLowerCase().includes(query) || 
    t.author.toLowerCase().includes(query)
  )
}

onMounted(() => fetchData())
</script>

<template>
  <div class="w-full flex flex-col z-10 animate-fade-in">
    
    <div class="mb-10">
      <h2 class="text-2xl font-bold text-white flex items-center gap-3 mb-6">
        <span class="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
           <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </span>
        Плейлисты
      </h2>

      <div v-if="isLoading" class="w-full flex justify-center py-10">
         <svg class="animate-spin h-8 w-8 text-indigo-500" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
      </div>

      <div v-else>
        <div v-if="isOwner && playlists.length < 2" class="flex gap-2 mb-6">
          <input v-model="newPlaylistName" type="text" placeholder="Название нового плейлиста..." class="flex-1 bg-gray-900/60 border border-gray-800 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-indigo-500 transition-colors" @keyup.enter="createPlaylist" />
          <button @click="createPlaylist" class="bg-indigo-600 hover:bg-indigo-500 px-6 py-2 rounded-xl font-bold transition-colors shadow-lg">Создать</button>
        </div>

        <div v-if="playlists.length === 0" class="bg-gray-900/40 border border-gray-800/80 rounded-3xl p-10 flex flex-col items-center justify-center text-center opacity-70">
          <svg class="w-12 h-12 mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
          <p class="text-lg font-semibold">У пользователя нет плейлистов</p>
        </div>

        <div class="grid grid-cols-1 gap-6">
          <div v-for="pl in playlists" :key="pl.name" class="bg-gray-900/60 border border-gray-800/80 rounded-2xl overflow-hidden shadow-lg flex flex-col">
            <div class="bg-gray-900 border-b border-gray-800 p-4 flex justify-between items-center">
              <div>
                <h3 class="font-bold text-lg text-white flex items-center gap-2">🎵 {{ pl.name }}</h3>
                <p class="text-xs text-gray-500 font-medium mt-1">Треков: {{ pl.tracks.length }}/50</p>
              </div>
              <button v-if="isOwner" @click="requestDeletePlaylist(pl.name)" class="p-2 text-red-400 bg-red-500/10 hover:bg-red-500/20 rounded-lg transition-colors"><IconTrash class="w-5 h-5" /></button>
            </div>
            
            <div class="p-4">
              <div v-if="isOwner && pl.tracks.length < 50" class="flex gap-2 mb-3">
                <input v-model="trackQueries[pl.name]" type="text" placeholder="Найти песню..." class="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors" @keyup.enter="addTrack(pl.name)" />
                <button @click="addTrack(pl.name)" :disabled="isSearching[pl.name]" class="bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm font-bold transition-colors border border-gray-700 disabled:opacity-50">
                  {{ isSearching[pl.name] ? '...' : 'Добавить' }}
                </button>
              </div>

              <div v-if="isOwner && pl.tracks.length < 50" class="flex gap-2 mb-4">
                <input v-model="importUrls[pl.name]" type="text" placeholder="Ссылка на плейлист (YT/VK/YM)..." class="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-purple-500 transition-colors" @keyup.enter="importPlaylistTracks(pl.name)" />
                <button @click="importPlaylistTracks(pl.name)" :disabled="isImporting[pl.name]" class="bg-purple-600/20 text-purple-400 hover:bg-purple-600/30 px-4 py-2 rounded-lg text-sm font-bold transition-colors border border-purple-500/30 disabled:opacity-50">
                  {{ isImporting[pl.name] ? '...' : 'Импорт' }}
                </button>
              </div>

              <div v-if="pl.tracks.length > 0" class="flex items-center gap-2 mb-4 bg-gray-950/50 border border-gray-800 rounded-lg px-3 py-1.5 focus-within:border-indigo-500/50 transition-colors">
                <IconSearch class="w-4 h-4 text-gray-500" />
                <input v-model="filterQueries[pl.name]" type="text" placeholder="Поиск в этом плейлисте..." class="flex-1 bg-transparent border-none text-sm text-white focus:outline-none placeholder-gray-600" />
              </div>

              <div v-if="pl.tracks.length === 0" class="text-center py-4 text-gray-500 text-sm">Плейлист пуст</div>
              <div v-else class="flex flex-col gap-2 max-h-80 overflow-y-auto pr-2 custom-scrollbar">
                <div v-for="t in getFilteredTracks(pl.name, pl.tracks)" :key="t.originalIndex" class="flex items-center justify-between p-3 bg-gray-950/50 rounded-xl border border-gray-800/50 group hover:border-gray-700 transition-colors">
                  <div class="overflow-hidden flex-1">
                    <div class="text-sm font-bold text-gray-200 truncate">{{ t.author }} - {{ t.title }}</div>
                    <div class="text-[10px] text-gray-500 uppercase mt-0.5">{{ t.source }}</div>
                  </div>
                  <button v-if="isOwner" @click="requestDeleteTrack(pl.name, t.originalIndex)" class="text-gray-500 hover:text-red-400 p-1.5 opacity-0 group-hover:opacity-100 transition-all flex-shrink-0">
                    <IconTrash class="w-5 h-5" />
                  </button>
                </div>
                <div v-if="getFilteredTracks(pl.name, pl.tracks).length === 0" class="text-center py-4 text-gray-500 text-sm">Ничего не найдено</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div>
      <h2 class="text-2xl font-bold text-white flex items-center gap-3 mb-6">
        <span class="p-2 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
           <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
        </span>
        Личный топ прослушиваний
      </h2>

      <div class="bg-gray-900/60 border border-gray-800/80 rounded-3xl p-6 shadow-lg min-h-[300px] relative overflow-hidden">
        <div v-if="isLoading" class="absolute inset-0 flex items-center justify-center bg-gray-950/50 z-20 backdrop-blur-sm">
           <svg class="animate-spin h-8 w-8 text-purple-500" viewBox="0 0 24 24" fill="none"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
        </div>

        <div v-if="topTracks.length === 0 && !isLoading" class="flex flex-col items-center justify-center py-16 opacity-50">
          <svg class="w-12 h-12 mb-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"></path></svg>
          <p class="text-lg font-semibold">Статистика пока пуста</p>
        </div>

        <div v-else class="flex flex-col gap-3">
          <div v-for="item in topTracks" :key="item.rank" class="flex items-center justify-between p-4 rounded-2xl bg-gray-950/40 border border-gray-800/50 hover:bg-gray-800/50 transition-colors group">
              <div class="flex items-center gap-5">
                <div class="w-10 h-10 flex items-center justify-center font-bold text-lg">
                   <span v-if="item.rank === 1" class="text-3xl filter drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]">🥇</span>
                   <span v-else-if="item.rank === 2" class="text-3xl">🥈</span>
                   <span v-else-if="item.rank === 3" class="text-3xl">🥉</span>
                   <span v-else class="text-gray-500 bg-gray-800 w-8 h-8 rounded-full flex items-center justify-center text-sm border border-gray-700">#{{ item.rank }}</span>
                </div>
                <div class="flex items-center gap-3">
                  <div>
                    <div class="font-bold text-gray-200 group-hover:text-white transition-colors text-base">{{ item.track_name.split(' - ')[1] || item.track_name }}</div>
                    <div class="text-sm text-gray-500">{{ item.track_name.split(' - ')[0] }}</div>
                  </div>
                </div>
              </div>
              <div class="text-right">
                 <span class="font-black text-purple-400 bg-purple-500/10 px-3 py-1 rounded-lg border border-purple-500/20">{{ item.play_count }} <span class="text-xs font-medium">раз</span></span>
              </div>
          </div>
        </div>
      </div>
    </div>

    <ConfirmModal :isOpen="!!trackToDelete" :isProcessing="isDeletingTrack" type="danger" title="Удаление трека" confirmText="Да, удалить" cancelText="Отмена" @confirm="confirmDeleteTrack" @cancel="trackToDelete = null">
      Вы уверены, что хотите удалить этот трек из плейлиста?
    </ConfirmModal>

    <ConfirmModal :isOpen="!!playlistToDelete" :isProcessing="isDeletingPlaylist" type="danger" title="Удаление плейлиста" confirmText="Удалить всё" cancelText="Отмена" @confirm="confirmDeletePlaylist" @cancel="playlistToDelete = null">
      Это действие полностью удалит плейлист <b>{{ playlistToDelete }}</b> и все песни в нём.
    </ConfirmModal>

  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: #374151; border-radius: 10px; }
</style>