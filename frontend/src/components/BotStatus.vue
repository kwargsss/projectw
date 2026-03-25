<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['updateStats'])
const botStatus = ref<'connecting' | 'online' | 'offline'>('connecting')
let statusInterval: ReturnType<typeof setInterval> | null = null
const API_URL = import.meta.env.VITE_API_BASE_URL

const fetchBotStats = async () => {
  try {
    const statsRes = await fetch(`${API_URL}/stats`, { credentials: 'include' })
    if (statsRes.ok) {
      const result = await statsRes.json()
      if (result.status === 'ok') {
        botStatus.value = 'online'
        emit('updateStats', result.data)
      } else {
        botStatus.value = 'offline'
        emit('updateStats', null)
      }
    } else {
      botStatus.value = 'offline'
      emit('updateStats', null)
    }
  } catch (err) {
    botStatus.value = 'offline'
    emit('updateStats', null)
  }
}

onMounted(async () => {
  await fetchBotStats()
  statusInterval = setInterval(fetchBotStats, 5000) 
})

onUnmounted(() => {
  if (statusInterval) clearInterval(statusInterval)
})
</script>

<template>
  <div class="flex items-center gap-2 px-3 py-1.5 rounded-full border border-gray-800 bg-gray-900/60 backdrop-blur-md transition-colors duration-300 shadow-sm"
       :class="{
         'text-yellow-400': botStatus === 'connecting',
         'text-green-400': botStatus === 'online',
         'text-red-400': botStatus === 'offline'
       }">
    
    <span class="relative flex h-2 w-2">
      <span v-if="botStatus !== 'offline'" class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
            :class="botStatus === 'online' ? 'bg-green-400' : 'bg-yellow-400'"></span>
      <span class="relative inline-flex rounded-full h-2 w-2"
            :class="{
              'bg-yellow-500': botStatus === 'connecting',
              'bg-green-500': botStatus === 'online',
              'bg-red-500': botStatus === 'offline'
            }"></span>
    </span>
    
    <span class="font-bold text-xs tracking-wider uppercase">
      {{ botStatus === 'connecting' ? 'Подключение' : (botStatus === 'online' ? 'Онлайн' : 'Оффлайн') }}
    </span>
  </div>
</template>