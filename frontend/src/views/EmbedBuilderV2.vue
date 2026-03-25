<script setup lang="ts">
import { ref, inject, computed, onMounted } from 'vue'
import { getAvatarUrl } from '../utils/helpers'
import { useToast } from '../utils/useToast'

const { showToast } = useToast()
const user = inject('user') as any
const botInfo = inject('botInfo') as any
const API_URL = import.meta.env.VITE_API_BASE_URL

const isSending = ref(false)
const channels = ref<{id: string, name: string}[]>([])

const settings = ref({ channel_id: '', color: '#5865F2' })

type BlockType = 'text_display' | 'media_gallery' | 'separator' | 'section' | 'file'
interface Block {
  id: number
  type: BlockType
  content?: string
  url?: string
  description?: string
  button_label?: string
  button_url?: string
}

const blocks = ref<Block[]>([])
let blockIdCounter = 0

onMounted(async () => {
  try {
    const res = await fetch(`${API_URL}/channels`, { credentials: 'include' })
    if (res.ok) channels.value = (await res.json()).data
  } catch (e) { console.error("Ошибка загрузки каналов") }
})

const addBlock = (type: BlockType) => {
  const newBlock: Block = { id: blockIdCounter++, type }
  blocks.value.push(newBlock)
}

const removeBlock = (index: number) => blocks.value.splice(index, 1)
const moveUp = (index: number) => { if (index > 0) [blocks.value[index - 1], blocks.value[index]] = [blocks.value[index], blocks.value[index - 1]] }
const moveDown = (index: number) => { if (index < blocks.value.length - 1) [blocks.value[index], blocks.value[index + 1]] = [blocks.value[index + 1], blocks.value[index]] }

const clearAll = () => {
  blocks.value = []
  settings.value.color = '#5865F2'
  showToast('Форма очищена', 'success')
}

const parseMarkdown = (text: string) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/^### (.*$)/gim, '<h4 class="text-base font-bold text-white mt-1 mb-1">$1</h4>')
    .replace(/^## (.*$)/gim, '<h3 class="text-lg font-bold text-white mt-2 mb-1">$1</h3>')
    .replace(/^# (.*$)/gim, '<h2 class="text-xl font-bold text-white mt-2 mb-1">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/__(.*?)__/g, '<u>$1</u>')
    .replace(/~~(.*?)~~/g, '<del>$1</del>')
    .replace(/`([^`]+)`/g, '<code class="bg-[#1e1f22] px-1.5 py-0.5 rounded-md font-mono text-[13px]">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-[#00a8fc] hover:underline">$1</a>')
    .replace(/\n/g, '<br/>')
}

const currentTime = computed(() => {
  const d = new Date()
  return `Сегодня в ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})

const sendEmbed = async () => {
  if (!settings.value.channel_id) return showToast('Выберите канал!', 'error')
  if (blocks.value.length === 0) return showToast('Добавьте хотя бы один блок!', 'error')
  
  isSending.value = true
  try {
    const payload = { channel_id: settings.value.channel_id, color: settings.value.color, blocks: blocks.value }
    const res = await fetch(`${API_URL}/embed/send_v2`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload), credentials: 'include'
    })
    
    if (res.ok) {
      showToast('V2 Embed отправлен!', 'success')
      blocks.value = [] 
    } else {
      const err = await res.json()
      showToast(`Ошибка: ${err.detail || 'Не удалось отправить'}`, 'error')
    }
  } catch (e) { showToast('Ошибка сети', 'error') } 
  finally { isSending.value = false }
}
</script>

<template>
  <div class="animate-fade-in pb-10 flex flex-col xl:flex-row gap-8 relative">
    
    <div class="w-full xl:w-[60%] space-y-6">
      
      <div class="bg-gray-900/40 backdrop-blur-md border border-gray-800 p-8 rounded-[2rem] shadow-lg relative flex justify-between items-center">
        <router-link to="/dashboard/embed" class="absolute top-4 left-4 text-gray-500 hover:text-white transition-colors flex items-center gap-1 text-sm font-bold">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" /></svg> Назад
        </router-link>
        
        <div class="mt-4">
          <h2 class="text-3xl font-extrabold text-white mb-2 flex items-center gap-3">
            Components <span class="bg-indigo-500 text-white px-2 py-1 rounded-lg text-sm uppercase tracking-widest">V2</span>
          </h2>
          <p class="text-gray-400 font-medium">Сборка сообщения из блоков: Текст, Галерея, Разделители.</p>
        </div>
        
        <button @click="clearAll" class="bg-red-500/10 text-red-400 hover:bg-red-500/20 px-4 py-2 rounded-xl text-sm font-bold transition-colors">Очистить всё</button>
      </div>

      <div class="bg-gray-900/60 border border-gray-800 p-6 rounded-3xl grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Канал для отправки</label>
          <div class="relative">
            <select v-model="settings.channel_id" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-indigo-500 outline-none appearance-none cursor-pointer">
              <option value="" disabled>Выберите канал</option>
              <option v-for="c in channels" :key="c.id" :value="c.id"># {{ c.name }}</option>
            </select>
            <svg class="w-5 h-5 text-gray-400 absolute right-4 top-3.5 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Цвет Контейнера</label>
          <div class="flex items-center gap-3 bg-gray-950 border border-gray-700 px-3 py-2 rounded-xl focus-within:border-indigo-500 transition-all">
            <input v-model="settings.color" type="color" class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent p-0">
            <input v-model="settings.color" type="text" class="flex-1 bg-transparent text-white outline-none font-mono text-sm uppercase">
          </div>
        </div>
      </div>

      <div class="space-y-4">
        <transition-group name="list">
          <div v-for="(block, index) in blocks" :key="block.id" class="bg-gray-900/80 border border-gray-700 p-5 rounded-3xl relative group">
            
            <div class="absolute right-4 top-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button @click="moveUp(index)" class="p-1 text-gray-400 hover:text-white bg-gray-800 rounded-lg"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg></button>
              <button @click="moveDown(index)" class="p-1 text-gray-400 hover:text-white bg-gray-800 rounded-lg"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg></button>
              <button @click="removeBlock(index)" class="p-1 text-red-400 hover:text-red-300 bg-red-900/30 rounded-lg ml-2"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
            </div>

            <div v-if="block.type === 'text_display'">
              <span class="text-xs font-extrabold text-blue-400 uppercase mb-3 block tracking-widest flex items-center gap-2"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h8m-8 6h16" /></svg> Text Display</span>
              <textarea v-model="block.content" rows="3" placeholder="Введите текст (Поддерживает Markdown и ## Заголовки)..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-blue-500"></textarea>
            </div>

            <div v-else-if="block.type === 'media_gallery'">
              <span class="text-xs font-extrabold text-green-400 uppercase mb-3 block tracking-widest flex items-center gap-2"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg> Media Gallery</span>
              <input v-model="block.url" type="text" placeholder="URL изображения (https://...)" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-green-500 mb-3">
              <input v-model="block.description" type="text" placeholder="Описание изображения (Alt text)..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-green-500">
            </div>

            <div v-else-if="block.type === 'separator'" class="flex items-center justify-center py-4">
              <span class="text-xs font-extrabold text-gray-500 uppercase tracking-widest flex items-center gap-4 w-full">
                <div class="h-px bg-gray-700 flex-1"></div> Separator <div class="h-px bg-gray-700 flex-1"></div>
              </span>
            </div>

            <div v-else-if="block.type === 'section'">
              <span class="text-xs font-extrabold text-pink-400 uppercase mb-3 block tracking-widest flex items-center gap-2"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg> Section (Секция с Кнопкой)</span>
              <input v-model="block.content" type="text" placeholder="Текст слева..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-pink-500 mb-3">
              <div class="flex gap-4">
                <input v-model="block.button_label" type="text" placeholder="Текст на кнопке" class="w-1/3 bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-pink-500">
                <input v-model="block.button_url" type="text" placeholder="URL Ссылки (https://...)" class="w-2/3 bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-pink-500">
              </div>
            </div>

            <div v-else-if="block.type === 'file'">
              <span class="text-xs font-extrabold text-yellow-400 uppercase mb-3 block tracking-widest flex items-center gap-2"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg> File (Файл)</span>
              <input v-model="block.url" type="text" placeholder="Прямая URL ссылка на файл (Например: .pdf, .zip)..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-yellow-500">
            </div>

          </div>
        </transition-group>

        <div class="mt-8 bg-gray-900/60 border border-gray-800 p-6 rounded-3xl">
          <h3 class="text-xs font-extrabold text-gray-500 uppercase tracking-widest text-center mb-5">Добавить блок</h3>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            
            <button @click="addBlock('text_display')" class="flex flex-col items-center justify-center gap-3 bg-gray-950 hover:bg-blue-500/10 border border-gray-800 hover:border-blue-500/30 text-gray-400 hover:text-blue-400 py-4 px-2 rounded-2xl transition-all group shadow-sm">
              <svg class="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h8m-8 6h16" /></svg>
              <span class="text-xs font-bold">Текст</span>
            </button>
            
            <button @click="addBlock('media_gallery')" class="flex flex-col items-center justify-center gap-3 bg-gray-950 hover:bg-green-500/10 border border-gray-800 hover:border-green-500/30 text-gray-400 hover:text-green-400 py-4 px-2 rounded-2xl transition-all group shadow-sm">
              <svg class="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              <span class="text-xs font-bold">Галерея</span>
            </button>
            
            <button @click="addBlock('section')" class="flex flex-col items-center justify-center gap-3 bg-gray-950 hover:bg-pink-500/10 border border-gray-800 hover:border-pink-500/30 text-gray-400 hover:text-pink-400 py-4 px-2 rounded-2xl transition-all group shadow-sm">
              <svg class="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
              <span class="text-xs font-bold">Секция</span>
            </button>
            
            <button @click="addBlock('file')" class="flex flex-col items-center justify-center gap-3 bg-gray-950 hover:bg-yellow-500/10 border border-gray-800 hover:border-yellow-500/30 text-gray-400 hover:text-yellow-400 py-4 px-2 rounded-2xl transition-all group shadow-sm">
              <svg class="w-6 h-6 group-hover:scale-110 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <span class="text-xs font-bold">Файл</span>
            </button>
            
            <button @click="addBlock('separator')" class="flex flex-col items-center justify-center gap-3 bg-gray-950 hover:bg-gray-400/10 border border-gray-800 hover:border-gray-400/30 text-gray-400 hover:text-gray-300 py-4 px-2 rounded-2xl transition-all group shadow-sm">
              <span class="font-extrabold text-xl mb-0.5 group-hover:scale-110 transition-transform">---</span>
              <span class="text-xs font-bold">Разделитель</span>
            </button>
            
          </div>
        </div>

      </div>
    </div>

    <div class="w-full xl:w-[40%] relative">
      <div class="sticky top-6 flex flex-col gap-6">
        
        <div class="bg-[#313338] rounded-2xl shadow-2xl overflow-hidden border border-gray-800">
          <div class="bg-[#2b2d31] px-5 py-3 border-b border-[#1e1f22] flex items-center gap-2 text-[#f2f3f5] font-bold text-sm uppercase">
            <svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg> Предпросмотр V2
          </div>
          
          <div class="p-5 font-sans text-[15px] text-[#dbdee1] leading-[1.375rem]">
            <div class="flex gap-4">
              <img :src="getAvatarUrl(botInfo.id, botInfo.avatar)" class="w-10 h-10 rounded-full mt-0.5 object-cover" />
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-1.5 mb-2">
                  <span class="font-medium text-[#f2f3f5]">{{ botInfo.username }}</span>
                  <span class="bg-[#5865F2] text-[10px] px-1.5 py-[1px] rounded text-white font-medium">БОТ</span>
                  <span class="text-xs text-[#80848e] ml-1">{{ currentTime }}</span>
                </div>
                
                <div class="flex flex-col relative max-w-[520px]">
                  <div class="absolute left-0 top-0 bottom-0 w-1 rounded-[4px]" :style="{ backgroundColor: settings.color }"></div>
                  
                  <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-[4px] py-4 px-4 ml-1 flex flex-col gap-3">
                    
                    <template v-for="(block, idx) in blocks" :key="block.id">
                      
                      <div v-if="block.type === 'text_display'" class="whitespace-pre-wrap break-words" v-html="parseMarkdown(block.content || '')"></div>
                      
                      <div v-else-if="block.type === 'media_gallery'" class="w-full">
                        <img v-if="block.url" :src="block.url" class="rounded-[8px] max-w-full max-h-[300px] object-cover" />
                      </div>
                      
                      <hr v-else-if="block.type === 'separator'" class="border-[#1e1f22] my-1 w-full" />
                      
                      <div v-else-if="block.type === 'section'" class="flex items-center justify-between gap-4">
                        <div class="flex-1 break-words font-medium" v-html="parseMarkdown(block.content || '')"></div>
                        <a v-if="block.button_label" :href="block.button_url || '#'" target="_blank" class="flex-shrink-0 bg-[#4e5058] hover:bg-[#6d6f78] transition-colors px-4 py-1.5 rounded-[4px] text-white text-sm font-medium flex items-center gap-2">
                          {{ block.button_label }}
                          <svg class="w-3.5 h-3.5 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        </a>
                      </div>

                      <div v-else-if="block.type === 'file' && block.url" class="bg-[#2b2d31] border border-[#1e1f22] rounded-[8px] p-3 flex items-center gap-3">
                        <div class="p-2 bg-[#1e1f22] rounded"><svg class="w-6 h-6 text-[#dbdee1]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
                        <div class="flex flex-col"><span class="text-[#00a8fc] hover:underline cursor-pointer text-sm font-medium">{{ block.url.split('/').pop() || 'file' }}</span><span class="text-xs text-[#80848e]">Вложение</span></div>
                      </div>

                    </template>

                    <div class="flex items-center gap-2 mt-2 pt-2 border-t border-[#1e1f22]/50">
                       <img :src="getAvatarUrl(user?.id, user?.avatar, 32)" class="w-5 h-5 rounded-full object-cover" />
                       <span class="text-[11px] text-[#dbdee1] font-medium">Отправлено администратором: {{ user?.username }} • {{ currentTime }}</span>
                    </div>

                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

        <button @click="sendEmbed" :disabled="isSending || blocks.length === 0" class="w-full flex items-center justify-center gap-3 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-4 rounded-2xl font-extrabold text-lg transition-all shadow-lg disabled:opacity-50 disabled:cursor-wait">
          <span v-if="!isSending">Отправить</span>
          <span v-else>Отправка...</span>
        </button>
        
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.list-move, .list-enter-active, .list-leave-active { transition: all 0.4s ease; }
.list-enter-from, .list-leave-to { opacity: 0; transform: scale(0.9) translateY(20px); }
.list-leave-active { position: absolute; }
</style>