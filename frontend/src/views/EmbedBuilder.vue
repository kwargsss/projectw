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

const embed = ref({
  channel_id: '',
  content: '',
  color: '#5865F2',
  title: '',
  description: '',
  url: '',
  author_name: '',
  author_icon: '',
  author_url: '',
  image_url: '',
  thumbnail_url: '',
  fields: [] as { name: string, value: string, inline: boolean }[]
})

onMounted(async () => {
  try {
    const res = await fetch(`${API_URL}/channels`, { credentials: 'include' })
    if (res.ok) {
      const result = await res.json()
      channels.value = result.data
    }
  } catch (e) {
    console.error("Не удалось загрузить каналы")
  }
})

const parseMarkdown = (text: string) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/__(.*?)__/g, '<u>$1</u>')
    .replace(/~~(.*?)~~/g, '<del>$1</del>')
    .replace(/`([^`]+)`/g, '<code class="bg-[#1e1f22] px-1.5 py-0.5 rounded-md font-mono text-[13px]">$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-[#00a8fc] hover:underline">$1</a>')
    .replace(/\n/g, '<br/>')
}

const addField = () => {
  if (embed.value.fields.length < 25) embed.value.fields.push({ name: 'Новое поле', value: 'Значение', inline: false })
  else showToast('Максимум 25 полей!', 'error')
}
const removeField = (index: number) => embed.value.fields.splice(index, 1)

const clearEmbed = () => {
  embed.value = {
    channel_id: embed.value.channel_id,
    content: '', color: '#5865F2', title: '', description: '', url: '',
    author_name: '', author_icon: '', author_url: '', image_url: '', thumbnail_url: '', fields: []
  }
  showToast('Форма очищена', 'success')
}

const currentTime = computed(() => {
  const d = new Date()
  return `Сегодня в ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})

const sendEmbed = async () => {
  if (!embed.value.channel_id) return showToast('Выберите канал!', 'error')
  
  isSending.value = true
  try {
    const res = await fetch(`${API_URL}/embed/send`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(embed.value), credentials: 'include'
    })
    
    if (res.ok) {
      showToast('Embed успешно отправлен боту!', 'success')
      const currentChannel = embed.value.channel_id
      embed.value = {
        channel_id: currentChannel,
        content: '', color: '#5865F2', title: '', description: '', url: '',
        author_name: '', author_icon: '', author_url: '', image_url: '', thumbnail_url: '', fields: []
      }
    } else {
      const err = await res.json()
      showToast(`Ошибка: ${err.detail || 'Не удалось отправить'}`, 'error')
    }
  } catch (e) {
    showToast('Ошибка сети', 'error')
  } finally {
    isSending.value = false
  }
}
</script>

<template>
  <div class="animate-fade-in pb-10 flex flex-col xl:flex-row gap-8 relative">
    
    <div class="w-full xl:w-[60%] space-y-6">
      
      <div class="bg-gray-900/40 backdrop-blur-md border border-gray-800 p-8 rounded-[2rem] shadow-lg relative overflow-hidden flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div class="absolute top-0 right-0 w-64 h-64 bg-pink-500/10 blur-[100px] rounded-full pointer-events-none"></div>
        <div class="relative z-10">
          <h2 class="text-3xl font-extrabold text-white mb-2">Конструктор <span class="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Embed</span></h2>
          <p class="text-gray-400 font-medium">Создавайте красивые сообщения от имени бота.</p>
        </div>
        
        <button @click="clearEmbed" class="relative z-10 bg-red-500/10 text-red-400 hover:bg-red-500/20 border border-red-500/20 px-4 py-2 rounded-xl text-sm font-bold transition-colors flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" /></svg>
          Очистить
        </button>
      </div>

      <router-link to="/dashboard/embed_v2" class="block w-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/30 p-5 rounded-3xl hover:bg-indigo-500/20 transition-all group cursor-pointer relative overflow-hidden shadow-lg hover:shadow-indigo-500/10">
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent translate-x-[-100%] group-hover:animate-[shimmer_1.5s_infinite]"></div>
        <div class="flex items-center justify-between relative z-10">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-indigo-500/20 rounded-xl text-indigo-400">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" /></svg>
            </div>
            <div>
              <h3 class="text-lg font-bold text-white flex items-center gap-2">Попробуйте новый Components V2 <span class="bg-indigo-500 text-white text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-wider">New</span></h3>
              <p class="text-sm text-gray-400">Модульный конструктор сообщений с блочной структурой.</p>
            </div>
          </div>
          <svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-indigo-400 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
        </div>
      </router-link>

      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg space-y-4">
        <h3 class="text-lg font-bold text-purple-400 flex items-center gap-2 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          Основные данные
        </h3>
        
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Выберите канал</label>
          <div class="relative">
            <select v-model="embed.channel_id" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all outline-none appearance-none cursor-pointer">
              <option value="" disabled>Выберите канал</option>
              <option v-for="c in channels" :key="c.id" :value="c.id"># {{ c.name }}</option>
            </select>
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-gray-400 absolute right-4 top-3.5 pointer-events-none" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" /></svg>
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex justify-between">
            Обычный текст (вне рамки) <span class="text-gray-600 font-normal">Поддерживает Markdown</span>
          </label>
          <textarea v-model="embed.content" rows="2" placeholder="**Всем привет!** Смотрите обновление..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-purple-500 focus:ring-1 focus:ring-purple-500 transition-all outline-none resize-none"></textarea>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Цвет рамки</label>
          <div class="flex items-center gap-3 bg-gray-950 border border-gray-700 px-3 py-2 rounded-xl focus-within:border-purple-500 transition-all">
            <input v-model="embed.color" type="color" class="w-8 h-8 rounded cursor-pointer border-0 bg-transparent p-0">
            <input v-model="embed.color" type="text" class="flex-1 bg-transparent text-white outline-none font-mono text-sm uppercase">
          </div>
        </div>
      </div>

      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg space-y-4">
        <h3 class="text-lg font-bold text-pink-400 flex items-center gap-2 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
          Автор
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Имя автора</label>
            <input v-model="embed.author_name" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-pink-500 transition-all">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">URL Аватарки автора</label>
            <input v-model="embed.author_icon" type="text" placeholder="https://..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-pink-500 transition-all">
          </div>
        </div>
      </div>

      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg space-y-4">
        <h3 class="text-lg font-bold text-indigo-400 flex items-center gap-2 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h7" /></svg>
          Содержимое
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Заголовок (Title)</label>
            <input v-model="embed.title" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-indigo-500 transition-all">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">URL Заголовка</label>
            <input v-model="embed.url" type="text" placeholder="https://..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-indigo-500 transition-all">
          </div>
        </div>
        <div>
          <label class="block text-xs font-bold text-gray-400 uppercase mb-2 flex justify-between">
            Описание (Description) <span class="text-gray-600 font-normal">Поддерживает Markdown</span>
          </label>
          <textarea v-model="embed.description" rows="4" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl outline-none focus:border-indigo-500 transition-all resize-y"></textarea>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Большое Изображение (URL)</label>
            <input v-model="embed.image_url" type="text" placeholder="https://..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-indigo-500 transition-all">
          </div>
          <div>
            <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Миниатюра справа (Thumbnail)</label>
            <input v-model="embed.thumbnail_url" type="text" placeholder="https://..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl outline-none focus:border-indigo-500 transition-all">
          </div>
        </div>
      </div>

      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-lg font-bold text-blue-400 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg>
            Поля (Fields)
          </h3>
          <button @click="addField" class="bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 px-4 py-1.5 rounded-lg text-sm font-bold transition-colors flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" /></svg>
            Добавить
          </button>
        </div>
        
        <div class="space-y-4">
          <div v-for="(field, index) in embed.fields" :key="index" class="bg-gray-950 border border-gray-800 p-4 rounded-2xl relative group">
            <button @click="removeField(index)" class="absolute top-3 right-3 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
            </button>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3 pr-8">
              <div>
                <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Название поля</label>
                <input v-model="field.name" type="text" class="w-full bg-gray-900 border border-gray-700 text-white px-3 py-2 rounded-xl outline-none focus:border-blue-500">
              </div>
              <div class="flex items-end mb-2">
                <label class="flex items-center gap-2 cursor-pointer group/cb">
                  <div class="w-5 h-5 rounded border border-gray-600 group-hover/cb:border-blue-500 flex items-center justify-center transition-colors" :class="field.inline ? 'bg-blue-500 border-blue-500' : 'bg-gray-900'">
                    <svg v-if="field.inline" class="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </div>
                  <input type="checkbox" v-model="field.inline" class="hidden">
                  <span class="text-sm font-bold text-gray-400 group-hover/cb:text-gray-300">В линию (Inline)</span>
                </label>
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 uppercase mb-1">Значение поля</label>
              <textarea v-model="field.value" rows="2" class="w-full bg-gray-900 border border-gray-700 text-white px-3 py-2 rounded-xl outline-none focus:border-blue-500 resize-y"></textarea>
            </div>
          </div>
          <div v-if="embed.fields.length === 0" class="text-center py-6 text-gray-500 font-medium border border-dashed border-gray-700 rounded-2xl">
            Поля отсутствуют
          </div>
        </div>
      </div>

    </div>

    <div class="w-full xl:w-[40%] relative">
      
      <div class="sticky top-6 flex flex-col gap-6">
        
        <div class="bg-[#313338] rounded-2xl shadow-2xl overflow-hidden border border-gray-800">
          <div class="bg-[#2b2d31] px-5 py-3 border-b border-[#1e1f22] flex items-center justify-between">
            <span class="text-[#f2f3f5] font-bold text-sm uppercase tracking-wider flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
              Предпросмотр
            </span>
          </div>
          
          <div class="p-5 font-sans text-[15px] text-[#dbdee1] leading-[1.375rem] max-w-full overflow-x-auto">
            <div class="flex gap-4">
              <img :src="getAvatarUrl(botInfo.id, botInfo.avatar)" class="w-10 h-10 rounded-full mt-0.5 object-cover cursor-pointer hover:opacity-80" />
              
              <div class="flex-1 min-w-0">
                <div class="flex items-baseline gap-1.5 mb-1">
                  <span class="font-medium text-[#f2f3f5] hover:underline cursor-pointer">{{ botInfo.username }}</span>
                  <span class="bg-[#5865F2] text-[10px] px-1.5 py-[1px] rounded flex items-center gap-1 text-white font-medium select-none">
                    <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg> БОТ
                  </span>
                  <span class="text-xs text-[#80848e] ml-1 select-none">{{ currentTime }}</span>
                </div>
                
                <div v-if="embed.content" class="mb-2 whitespace-pre-wrap break-words" v-html="parseMarkdown(embed.content)"></div>
                
                <div class="flex flex-col relative mt-1 max-w-[520px]">
                  <div class="absolute left-0 top-0 bottom-0 w-1 rounded-l-[4px]" :style="{ backgroundColor: embed.color || '#202225' }"></div>
                  
                  <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-r-[4px] p-4 pl-4 flex gap-4">
                    <div class="flex flex-col min-w-0 flex-1">
                      
                      <div v-if="embed.author_name" class="flex items-center gap-2 mb-2 min-w-0">
                         <img v-if="embed.author_icon" :src="embed.author_icon" class="w-6 h-6 rounded-full object-cover" />
                         <span class="font-semibold text-[#f2f3f5] text-sm break-words">{{ embed.author_name }}</span>
                      </div>
                      
                      <a v-if="embed.title && embed.url" :href="embed.url" target="_blank" class="font-bold text-[#00a8fc] text-base mb-2 hover:underline cursor-pointer break-words">{{ embed.title }}</a>
                      <div v-else-if="embed.title" class="font-bold text-[#f2f3f5] text-base mb-2 break-words">{{ embed.title }}</div>
                      
                      <div v-if="embed.description" class="whitespace-pre-wrap text-sm mb-3 break-words" v-html="parseMarkdown(embed.description)"></div>
                      
                      <div v-if="embed.fields.length" class="flex flex-row flex-wrap gap-x-[15px] gap-y-3 mb-3">
                         <div v-for="(f, i) in embed.fields" :key="i" :class="f.inline ? 'w-[calc(33.33%-10px)] min-w-[120px]' : 'w-full'">
                            <div class="font-bold text-[#f2f3f5] text-[13px] mb-0.5 break-words" v-html="parseMarkdown(f.name)"></div>
                            <div class="text-[13px] break-words text-[#dbdee1]" v-html="parseMarkdown(f.value)"></div>
                         </div>
                      </div>
                      
                      <img v-if="embed.image_url" :src="embed.image_url" class="rounded max-w-full max-h-[300px] object-cover mb-3" />
                      
                      <div class="flex items-center gap-2 mt-2">
                         <img :src="getAvatarUrl(user?.id, user?.avatar, 32)" class="w-5 h-5 rounded-full object-cover" />
                         <span class="text-[11px] text-[#dbdee1] font-medium">Отправлено администратором: {{ user?.username }} • {{ currentTime }}</span>
                      </div>
                    </div>
                    
                    <div v-if="embed.thumbnail_url" class="flex-shrink-0 ml-4">
                      <img :src="embed.thumbnail_url" class="w-20 h-20 rounded object-cover" />
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </div>
        </div>

        <button @click="sendEmbed" :disabled="isSending" class="w-full flex items-center justify-center gap-3 bg-purple-600 hover:bg-purple-500 text-white px-6 py-4 rounded-2xl font-extrabold text-lg transition-all shadow-[0_0_20px_rgba(147,51,234,0.3)] hover:shadow-[0_0_30px_rgba(168,85,247,0.5)] hover:-translate-y-1 disabled:opacity-50 disabled:cursor-wait disabled:hover:translate-y-0">
          <svg v-if="isSending" class="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          <span v-if="!isSending">Отправить</span>
          <span v-else>Отправка...</span>
        </button>
        
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

@keyframes shimmer {
  100% { transform: translateX(100%); }
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4b5563; }
</style>