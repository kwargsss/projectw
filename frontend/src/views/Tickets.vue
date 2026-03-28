<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import IconGamepad from '../components/icons/IconGamepad.vue'
import IconWrench from '../components/icons/IconWrench.vue'
import IconArchive from '../components/icons/IconArchive.vue'

const router = useRouter()
const tickets = ref<any[]>([])
const activeCategory = ref('server') 
let pollingInterval: any = null

const API_URL = import.meta.env.VITE_API_BASE_URL

const fetchTickets = async () => {
    try {
        const response = await fetch(`${API_URL}/tickets`, { credentials: 'include' })
        if (!response.ok) return
        
        const data = await response.json()
        if (data.status === 'ok') {
            tickets.value = data.data
        }
    } catch (e) {
    }
}

const filteredTickets = computed(() => {
    return tickets.value.filter(t => {
        if (activeCategory.value === 'archived') {
            return t.status === 'archived' || t.status === 'closed'
        }
        return t.type === activeCategory.value && t.status === 'open'
    })
})

const getStatusColor = (status: string) => {
    if (status === 'open') return 'text-green-400 bg-green-400/10 border-green-400/20'
    if (status === 'closed') return 'text-red-400 bg-red-400/10 border-red-400/20'
    return 'text-gray-400 bg-gray-500/10 border-gray-500/20'
}

onMounted(() => {
    fetchTickets()
    pollingInterval = setInterval(fetchTickets, 5000) 
})

onUnmounted(() => {
    if (pollingInterval) clearInterval(pollingInterval)
})
</script>

<template>
    <div class="p-8 space-y-8 animate-fade-in">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-extrabold text-white mb-2">Обращения</h1>
                <p class="text-gray-400 font-medium">Управление запросами пользователей сервера.</p>
            </div>
        </div>
        
        <div class="flex gap-2 bg-gray-900/60 p-1.5 rounded-2xl w-max border border-gray-800 shadow-sm backdrop-blur-md">
            <button @click="activeCategory = 'server'" :class="{'bg-purple-600 text-white shadow-md': activeCategory === 'server', 'text-gray-400 hover:text-white hover:bg-gray-800': activeCategory !== 'server'}" class="px-5 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2">
                <IconGamepad class="w-5 h-5" /> Серверные
            </button>
            <button @click="activeCategory = 'tech'" :class="{'bg-purple-600 text-white shadow-md': activeCategory === 'tech', 'text-gray-400 hover:text-white hover:bg-gray-800': activeCategory !== 'tech'}" class="px-5 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2">
                <IconWrench class="w-5 h-5" /> Технические
            </button>
            <button @click="activeCategory = 'archived'" :class="{'bg-gray-700 text-white shadow-md': activeCategory === 'archived', 'text-gray-400 hover:text-white hover:bg-gray-800': activeCategory !== 'archived'}" class="px-5 py-2.5 rounded-xl font-bold transition-all flex items-center gap-2">
                <IconArchive class="w-5 h-5" /> Архив
            </button>
        </div>

        <div class="grid gap-4">
            <div v-if="filteredTickets.length === 0" class="text-gray-500 py-16 text-center bg-gray-900/40 rounded-3xl border border-gray-800 border-dashed backdrop-blur-sm flex flex-col items-center">
                <IconArchive class="w-14 h-14 mx-auto text-gray-600 mb-4" />
                <span class="text-lg font-bold">В данной категории пусто</span>
                <span class="text-sm mt-1">Новые обращения появятся здесь автоматически.</span>
            </div>

            <div v-for="ticket in filteredTickets" :key="ticket.id" 
                 @click="router.push(`/dashboard/tickets/${ticket.type}/${ticket.id}`)"
                 class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-5 rounded-2xl hover:border-purple-500/50 hover:bg-gray-800/80 cursor-pointer transition-all flex justify-between items-center group shadow-sm">
                
                <div class="flex items-center gap-5">
                    <div class="w-12 h-12 rounded-full bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 group-hover:bg-purple-500 group-hover:text-white transition-all duration-300">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                    </div>
                    
                    <div class="flex flex-col gap-1.5">
                        <div class="flex items-center gap-3">
                            <span class="text-xl font-extrabold text-white group-hover:text-purple-400 transition-colors">
                                {{ ticket.creator_name }}
                            </span>
                            <span class="bg-gray-800 text-gray-400 border border-gray-700 text-[10px] px-2 py-0.5 rounded-md font-bold uppercase tracking-wider">
                                #{{ ticket.name }}
                            </span>
                        </div>
                        <span class="text-xs text-gray-500 font-medium">
                            Открыто: {{ new Date(parseInt(ticket.created_at) * 1000).toLocaleString() }}
                        </span>
                    </div>
                </div>

                <div class="flex items-center gap-4">
                    <span :class="getStatusColor(ticket.status)" class="px-3 py-1.5 rounded-lg border font-bold text-xs uppercase tracking-wider">
                        {{ ticket.status === 'open' ? 'Открыт' : ticket.status === 'closed' ? 'Закрыт' : 'В архиве' }}
                    </span>
                    <div class="text-gray-500 group-hover:text-purple-400 transition-colors group-hover:translate-x-1 duration-300">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>