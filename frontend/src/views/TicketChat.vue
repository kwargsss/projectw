<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ConfirmModal from '../components/ConfirmModal.vue'

const route = useRoute()
const router = useRouter()
const ticketId = route.params.id as string
const type = route.params.type as string

const currentUser = inject('user') as any
const currentTicket = ref<any>(null)
const messages = ref<any[]>([])
const messageInput = ref('')
const chatContainer = ref<HTMLElement | null>(null)

const showCloseModal = ref(false)
const showDeleteModal = ref(false)
const showOpenModal = ref(false)
const showForceDeleteModal = ref(false)

const ticketStatus = ref('open')
const isProcessing = ref(false)
const transcriptHtml = ref('')

const API_URL = import.meta.env.VITE_API_BASE_URL

let ws: WebSocket | null = null

const scrollToBottom = async () => {
    await nextTick()
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
}

const connectWebSocket = () => {
    const wsUrl = API_URL.replace(/^http/, 'ws') + `/ws/tickets/${ticketId}`
    
    ws = new WebSocket(wsUrl)
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.is_bot && data.embeds && data.embeds.length > 0) {
            const embed = data.embeds[0]
            if (embed.footer && embed.footer.text && embed.footer.text.startsWith('Сотрудник поддержки:')) {
                data.author = embed.footer.text.replace('Сотрудник поддержки:', '').trim()
                data.avatar = embed.footer.icon_url || '/bot-avatar.png'
                data.is_bot = false
                data.is_admin_reply = true
                if (embed.description) data.content = embed.description
                data.embeds = [] 
            }
        }
        
        messages.value = messages.value.filter(m => !m.isTemp)
        messages.value.push(data)
        scrollToBottom()
    }

    ws.onclose = () => {
        setTimeout(connectWebSocket, 3000)
    }
}

const sendMessage = async () => {
    if (!messageInput.value.trim()) return
    const content = messageInput.value
    messageInput.value = ''
    
    const avatarUrl = currentUser?.value?.avatar 
        ? `https://cdn.discordapp.com/avatars/${currentUser.value.id}/${currentUser.value.avatar}.png` 
        : '/bot-avatar.png'
    
    const tempId = 'temp_' + Date.now()
    messages.value.push({
        id: tempId,
        isTemp: true,
        author: currentUser?.value?.username || 'Вы',
        avatar: avatarUrl,
        is_bot: false,
        is_admin_reply: true,
        timestamp: Math.floor(Date.now() / 1000),
        content: content,
        embeds: []
    })
    scrollToBottom()
    
    try {
        await fetch(`${API_URL}/tickets/${ticketId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
            credentials: 'include'
        })
    } catch (e) {
        messages.value = messages.value.filter(m => m.id !== tempId)
    }
}

const performAction = async (action: 'close' | 'open' | 'delete' | 'force_delete') => {
    isProcessing.value = true
    try {
        await fetch(`${API_URL}/tickets/${ticketId}/action?action=${action}`, { 
            method: 'POST',
            credentials: 'include'
        })

        if (action === 'delete' || action === 'force_delete') {
            router.push('/dashboard/tickets')
        } else {
            ticketStatus.value = action === 'close' ? 'closed' : 'open'
        }
    } finally {
        isProcessing.value = false
        showCloseModal.value = false
        showDeleteModal.value = false
        showOpenModal.value = false
        showForceDeleteModal.value = false
    }
}

const parseMarkdown = (text: string) => {
    if (!text) return ''
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/~~(.*?)~~/g, '<del>$1</del>')
        .replace(/`([^`]+)`/g, '<code class="bg-gray-800 px-1 py-0.5 rounded text-[12px] text-purple-400 border border-gray-700">$1</code>')
        .replace(/\n/g, '<br/>')
}

onMounted(async () => {
    try {
        const response = await fetch(`${API_URL}/tickets`, { credentials: 'include' })
        const data = await response.json()
        currentTicket.value = data.data?.find((t: any) => t.id === ticketId)
        
        if (currentTicket.value) {
            ticketStatus.value = currentTicket.value.status
            
            if (ticketStatus.value === 'archived') {
                const res = await fetch(`${API_URL}/tickets/${ticketId}/transcript`, { credentials: 'include' })
                if (res.ok) {
                    transcriptHtml.value = await res.text()
                }
            }
        }
    } catch (e) {
        console.error("Ошибка при получении статуса тикета:", e)
    }

    if (ticketStatus.value !== 'archived') {
        connectWebSocket()
    }
})

onUnmounted(() => {
    if (ws) ws.close()
})
</script>

<template>
    <div class="h-full flex flex-col relative animate-fade-in">
        <div class="px-6 py-5 flex items-center justify-between shrink-0">
            <div class="flex items-center gap-4">
                <button @click="router.push('/dashboard/tickets')" class="w-10 h-10 rounded-full bg-gray-900/80 border border-gray-700 flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-800 transition-colors shadow-sm">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                </button>
                <div>
                    <div class="flex items-center gap-2 mb-0.5">
                        <div class="w-6 h-6 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center shrink-0">
                            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clip-rule="evenodd" /></svg>
                        </div>
                        <h1 class="text-lg font-bold text-white leading-none">От: {{ currentTicket?.creator_name || 'Загрузка...' }}</h1>
                    </div>
                    <div class="flex items-center gap-2 mt-1">
                        <span class="text-[11px] text-gray-500 font-bold uppercase tracking-wider">#{{ currentTicket?.name || ticketId }}</span>
                        <span v-if="ticketStatus === 'closed'" class="bg-red-500/10 text-red-400 border border-red-500/20 text-[10px] px-2 py-[1px] rounded font-bold uppercase tracking-wider">Закрыт</span>
                        <span v-else-if="ticketStatus === 'archived'" class="bg-gray-600/20 text-gray-400 border border-gray-600/20 text-[10px] px-2 py-[1px] rounded font-bold uppercase tracking-wider">Архивный транскрипт</span>
                    </div>
                </div>
            </div>
            
            <div class="flex gap-2">
                <button v-if="ticketStatus === 'open'" @click="showCloseModal = true" class="px-4 py-2 bg-gray-900/80 hover:bg-red-500/20 text-gray-300 hover:text-red-400 border border-gray-700 hover:border-red-500/50 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
                    Закрыть тикет
                </button>
                <button v-if="ticketStatus === 'closed'" @click="showOpenModal = true" class="px-4 py-2 bg-green-500/10 hover:bg-green-500 text-green-500 hover:text-white border border-green-500/50 hover:border-green-500 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z"/></svg>
                    Открыть
                </button>
                
                <button v-if="ticketStatus === 'archived'" @click="showForceDeleteModal = true" class="px-4 py-2 bg-gray-900/80 hover:bg-red-500 text-gray-400 hover:text-white border border-gray-700 hover:border-red-500 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    Удалить архив
                </button>

                <button v-else-if="ticketStatus === 'closed'" @click="showDeleteModal = true" class="px-4 py-2 bg-gray-900/80 hover:bg-red-500 text-gray-400 hover:text-white border border-gray-700 hover:border-red-500 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-sm">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                    Удалить тикет
                </button>
            </div>
        </div>

        <div class="flex-1 overflow-hidden px-6 pb-6 flex flex-col relative z-10">
            <div class="flex-1 bg-gray-900/60 backdrop-blur-md border border-gray-800 rounded-3xl flex flex-col shadow-lg overflow-hidden">
                
                <div v-if="ticketStatus === 'archived'" class="flex-1 flex flex-col w-full h-full bg-[#36393e]">
                    <iframe v-if="transcriptHtml" :srcdoc="transcriptHtml" class="flex-1 w-full h-full min-h-[70vh] border-none"></iframe>
                    <div v-else class="flex-1 h-full flex items-center justify-center text-gray-500">Загрузка архива...</div>
                </div>

                <template v-else>
                    <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 sm:p-6 space-y-3 custom-scrollbar">
                        <div v-if="messages.length === 0" class="h-full flex flex-col items-center justify-center text-gray-500">
                            <div class="bg-gray-800/50 p-4 rounded-2xl mb-3 border border-gray-700/50">
                                <svg class="w-8 h-8 text-purple-500/80" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
                            </div>
                            <p class="font-semibold text-sm">История сообщений пуста</p>
                        </div>

                        <div v-for="msg in messages" :key="msg.id || msg.timestamp" 
                             class="flex gap-3 hover:bg-gray-800/40 p-2.5 -mx-2.5 rounded-2xl transition-colors group"
                             :class="{'opacity-50 pointer-events-none': msg.isTemp}">
                            
                            <img :src="msg.avatar || '/bot-avatar.png'" class="w-9 h-9 rounded-full object-cover shrink-0 mt-0.5 border border-gray-700/50" />
                            
                            <div class="flex-1 min-w-0">
                                <div class="flex items-baseline gap-2 mb-0.5">
                                    <span class="font-bold text-[13px] text-gray-200 tracking-wide" :class="{'text-purple-400': msg.is_bot}">{{ msg.author }}</span>
                                    
                                    <span v-if="msg.is_bot" class="bg-purple-500/20 text-purple-400 border border-purple-500/20 text-[9px] px-1.5 py-[1px] rounded uppercase font-bold tracking-wider">Bot</span>
                                    <span v-else-if="msg.is_admin_reply" class="bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 text-[9px] px-1.5 py-[1px] rounded uppercase font-bold tracking-wider flex items-center gap-1">
                                        <svg class="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                                        Поддержка
                                    </span>

                                    <span class="text-[11px] text-gray-500 font-medium">
                                        {{ new Date(msg.timestamp * 1000).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}
                                        <span v-if="msg.isTemp" class="italic ml-1">(Отправка...)</span>
                                    </span>
                                </div>
                                
                                <div v-if="msg.content" class="text-[13px] leading-relaxed break-words text-gray-300 bg-gray-800/50 w-fit px-3 py-2 rounded-xl rounded-tl-sm border border-gray-700/30" v-html="parseMarkdown(msg.content)"></div>
                                
                                <div v-for="(embed, idx) in msg.embeds" :key="idx" class="mt-2 flex max-w-2xl">
                                    <div class="w-1 rounded-l-lg shrink-0" :style="`background-color: ${embed.color ? '#' + embed.color.toString(16).padStart(6, '0') : '#8B5CF6'}`"></div>
                                    <div class="bg-gray-950/40 p-3 sm:p-4 rounded-r-lg shadow-sm border border-gray-800/80 border-l-0 w-full">
                                        <div v-if="embed.author" class="flex items-center gap-2 mb-2">
                                            <img v-if="embed.author.icon_url" :src="embed.author.icon_url" class="w-5 h-5 rounded-full object-cover" />
                                            <span class="font-bold text-[13px] text-gray-200">{{ embed.author.name }}</span>
                                        </div>
                                        <div v-if="embed.title" class="font-bold text-white text-[14px] mb-1.5" v-html="parseMarkdown(embed.title)"></div>
                                        <div v-if="embed.description" class="text-[13px] text-gray-400 leading-relaxed whitespace-pre-wrap" v-html="parseMarkdown(embed.description)"></div>
                                        
                                        <div v-if="embed.fields && embed.fields.length" class="mt-3 grid grid-cols-2 gap-3">
                                            <div v-for="field in embed.fields" :key="field.name" :class="{'col-span-2': !field.inline}">
                                                <div class="font-bold text-[12px] text-gray-300 mb-0.5" v-html="parseMarkdown(field.name)"></div>
                                                <div class="text-[12px] text-gray-500" v-html="parseMarkdown(field.value)"></div>
                                            </div>
                                        </div>
                                        
                                        <div v-if="embed.footer" class="mt-3 flex items-center gap-2 text-[11px] text-gray-500 font-medium pt-2.5 border-t border-gray-800/80">
                                            <img v-if="embed.footer.icon_url" :src="embed.footer.icon_url" class="w-4 h-4 rounded-full object-cover" />
                                            <span>{{ embed.footer.text }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="px-4 py-3 bg-gray-900/80 border-t border-gray-800 shrink-0">
                        <div class="relative flex items-center">
                            <input v-model="messageInput" @keyup.enter="sendMessage"
                                   :disabled="ticketStatus !== 'open'"
                                   :placeholder="ticketStatus === 'open' ? `Написать сообщение в тикет...` : 'Тикет закрыт. Откройте его, чтобы отправить сообщение.'"
                                   class="w-full bg-gray-950 border border-gray-800 text-[14px] text-gray-200 px-4 py-3 pr-14 rounded-xl focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all placeholder-gray-600 shadow-inner disabled:opacity-50" />
                            
                            <button @click="sendMessage" :disabled="!messageInput.trim() || ticketStatus !== 'open'"
                                    class="absolute right-2 p-2 bg-purple-600 hover:bg-purple-500 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
                            </button>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <ConfirmModal :isOpen="showCloseModal" :isProcessing="isProcessing" type="danger" @confirm="performAction('close')" @cancel="showCloseModal = false">
            <div class="text-center flex flex-col gap-2">
                <span class="text-lg font-bold text-white">Закрытие тикета</span>
                <span class="text-gray-400 text-sm">Вы уверены, что хотите закрыть это обращение? Пользователь больше не сможет писать в чат.</span>
            </div>
        </ConfirmModal>

        <ConfirmModal :isOpen="showOpenModal" :isProcessing="isProcessing" type="primary" @confirm="performAction('open')" @cancel="showOpenModal = false">
            <div class="text-center flex flex-col gap-2">
                <span class="text-lg font-bold text-white">Возобновление тикета</span>
                <span class="text-gray-400 text-sm">Пользователь снова получит доступ к каналу и сможет отправлять сообщения.</span>
            </div>
        </ConfirmModal>

        <ConfirmModal :isOpen="showDeleteModal" :isProcessing="isProcessing" type="danger" @confirm="performAction('delete')" @cancel="showDeleteModal = false">
            <div class="text-center flex flex-col gap-2">
                <span class="text-lg font-bold text-red-400">Удаление тикета</span>
                <span class="text-gray-400 text-sm">Это действие безвозвратно удалит канал в Discord. Архив переписки будет сохранен на сайте.</span>
            </div>
        </ConfirmModal>

        <ConfirmModal :isOpen="showForceDeleteModal" :isProcessing="isProcessing" type="danger" @confirm="performAction('force_delete')" @cancel="showForceDeleteModal = false">
            <div class="text-center flex flex-col gap-2">
                <span class="text-lg font-bold text-red-400">Удаление архива</span>
                <span class="text-gray-400 text-sm">Вы уверены? Это безвозвратно удалит запись о тикете и его HTML-транскрипт с сайта.</span>
            </div>
        </ConfirmModal>
    </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}
.custom-scrollbar::-webkit-scrollbar { width: 6px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background-color: rgba(75, 85, 99, 0.4); border-radius: 20px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: rgba(107, 114, 128, 0.8); }
</style>