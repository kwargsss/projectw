<script setup lang="ts">
import { ref, onMounted, watch, inject, computed } from 'vue'
import { getAvatarUrl } from '../utils/helpers'
import { useToast } from '../utils/useToast'
import UnsavedChangesPanel from '../components/UnsavedChangesPanel.vue'

const { showToast } = useToast()
const API_URL = import.meta.env.VITE_API_BASE_URL
const botInfo = inject('botInfo') as any

const isSaving = ref(false)
const isDirty = ref(false)
const channels = ref<{id: string, name: string}[]>([])

type BlockType = 'text_display' | 'media_gallery' | 'separator' | 'section' | 'file'
interface Block { id: number; type: BlockType; content?: string; url?: string; description?: string; button_label?: string; button_url?: string }

const originalSettings = ref<any>(null)
const settings = ref({
  welcome: { enabled: false, channel_id: '', embed_type: 'v1', content: '', title: '', description: '', color: '#5865F2', image_url: '', thumbnail_url: '', blocks: [] as Block[] },
  goodbye: { enabled: false, channel_id: '', embed_type: 'v1', content: '', title: '', description: '', color: '#ED4245', image_url: '', thumbnail_url: '', blocks: [] as Block[] }
})

onMounted(async () => {
  try {
    const chRes = await fetch(`${API_URL}/channels`, { credentials: 'include' })
    if (chRes.ok) channels.value = (await chRes.json()).data

    const setRes = await fetch(`${API_URL}/settings/notifications`, { credentials: 'include' })
    if (setRes.ok) {
      const data = (await setRes.json()).data
      if (data && data.welcome) {
        if (!data.welcome.blocks) data.welcome.blocks = []
        if (!data.goodbye.blocks) data.goodbye.blocks = []
        settings.value = data
        originalSettings.value = JSON.parse(JSON.stringify(data)) 
      }
    }
  } catch (e) { console.error("Ошибка загрузки") }
})

watch(settings, (newVal) => {
  if (originalSettings.value) {
    isDirty.value = JSON.stringify(newVal) !== JSON.stringify(originalSettings.value)
  }
}, { deep: true })

const resetSettings = () => {
  if (originalSettings.value) {
    settings.value = JSON.parse(JSON.stringify(originalSettings.value))
    showToast('Изменения отменены', 'success')
  }
}

const saveSettings = async () => {
  if (settings.value.welcome.enabled && !settings.value.welcome.channel_id) {
    return showToast('❌ Выберите канал для Приветствий!', 'error')
  }
  if (settings.value.goodbye.enabled && !settings.value.goodbye.channel_id) {
    return showToast('❌ Выберите канал для Прощаний!', 'error')
  }

  isSaving.value = true
  try {
    const res = await fetch(`${API_URL}/settings/notifications`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings.value), credentials: 'include'
    })
    if (res.ok) {
      showToast('Настройки успешно сохранены!', 'success')
      originalSettings.value = JSON.parse(JSON.stringify(settings.value))
      isDirty.value = false
    } else showToast('Ошибка при сохранении.', 'error')
  } catch (e) { showToast('Ошибка сети', 'error') } 
  finally { isSaving.value = false }
}

const parseVariables = (text: string) => {
  if (!text) return ''
  return text
    .replace(/\{user\}/g, '<span class="bg-[#5865F2]/30 text-[#c9cdfb] px-1 rounded cursor-pointer hover:bg-[#5865F2]/50 transition-colors font-medium">@Пользователь</span>')
    .replace(/\{user\.name\}/g, 'Пользователь')
    .replace(/\{server\}/g, 'Наш Сервер')
    .replace(/\{count\}/g, '1001')
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

const renderText = (text: string) => parseVariables(parseMarkdown(text))

const currentTime = computed(() => {
  const d = new Date()
  return `Сегодня в ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
})

const addBlock = (target: 'welcome' | 'goodbye', type: BlockType) => {
  settings.value[target].blocks.push({ id: Date.now(), type, content: '', url: '', description: '', button_label: '', button_url: '' })
}
const removeBlock = (target: 'welcome' | 'goodbye', index: number) => settings.value[target].blocks.splice(index, 1)
const moveUp = (target: 'welcome' | 'goodbye', index: number) => { if (index > 0) [settings.value[target].blocks[index - 1], settings.value[target].blocks[index]] = [settings.value[target].blocks[index], settings.value[target].blocks[index - 1]] }
const moveDown = (target: 'welcome' | 'goodbye', index: number) => { if (index < settings.value[target].blocks.length - 1) [settings.value[target].blocks[index], settings.value[target].blocks[index + 1]] = [settings.value[target].blocks[index + 1], settings.value[target].blocks[index]] }
</script>

<template>
  <div class="animate-fade-in pb-24 relative"> 
    
    <div class="bg-gray-900/40 backdrop-blur-md border border-gray-800 p-8 rounded-[2rem] shadow-lg relative flex flex-col gap-2 mb-8">
      <div class="absolute top-0 left-10 w-64 h-64 bg-green-500/10 blur-[100px] rounded-full pointer-events-none"></div>
      <div class="relative z-10">
        <h2 class="text-3xl font-extrabold text-white mb-2 flex items-center gap-3">
          <svg class="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" /></svg> Оповещения
        </h2>
        <p class="text-gray-400 font-medium">Настройте автоматические сообщения при входе и выходе участников.</p>
      </div>
    </div>

    <div class="bg-blue-900/20 border border-blue-800/50 p-4 rounded-2xl mb-8 flex items-start gap-4">
      <div class="p-2 bg-blue-500/20 rounded-xl text-blue-400"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div>
      <div>
        <h4 class="text-white font-bold mb-1">Доступные переменные (работают в Live Preview)</h4>
        <p class="text-sm text-blue-200/80">Используйте: <code class="bg-blue-950 px-1.5 py-0.5 rounded text-blue-300">{user}</code> (Упоминание), <code class="bg-blue-950 px-1.5 py-0.5 rounded text-blue-300">{user.name}</code> (Имя), <code class="bg-blue-950 px-1.5 py-0.5 rounded text-blue-300">{server}</code> (Имя сервера), <code class="bg-blue-950 px-1.5 py-0.5 rounded text-blue-300">{count}</code> (Кол-во участников).</p>
      </div>
    </div>

    <div class="flex flex-col gap-10">
      
      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 rounded-3xl shadow-lg overflow-hidden transition-all" :class="{'ring-2 ring-indigo-500/50': settings.welcome.enabled}">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center bg-gray-900/40">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-500/20 rounded-xl text-indigo-400"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" /></svg></div>
            <div><h3 class="text-lg font-bold text-white">Вход участника</h3><p class="text-xs text-gray-400">Приветственное сообщение</p></div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="settings.welcome.enabled" class="sr-only peer">
            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-500"></div>
          </label>
        </div>

        <div v-if="settings.welcome.enabled" class="p-6 animate-fade-in flex flex-col xl:flex-row gap-8">
          
          <div class="w-full xl:w-[55%] space-y-5">
            <div class="flex gap-4">
              <label class="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all" :class="settings.welcome.embed_type === 'v1' ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400' : 'bg-gray-950 border-gray-700 text-gray-400'">
                <input type="radio" v-model="settings.welcome.embed_type" value="v1" class="hidden"> Обычный Embed
              </label>
              <label class="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all" :class="settings.welcome.embed_type === 'v2' ? 'bg-indigo-500/10 border-indigo-500 text-indigo-400' : 'bg-gray-950 border-gray-700 text-gray-400'">
                <input type="radio" v-model="settings.welcome.embed_type" value="v2" class="hidden"> Components V2
              </label>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Канал</label>
                <select v-model="settings.welcome.channel_id" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-indigo-500 outline-none"><option value="" disabled>Выберите канал</option><option v-for="c in channels" :key="c.id" :value="c.id"># {{ c.name }}</option></select>
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Цвет Embed/Контейнера</label>
                <div class="flex items-center gap-2 bg-gray-950 border border-gray-700 px-3 py-1.5 rounded-xl focus-within:border-indigo-500"><input v-model="settings.welcome.color" type="color" class="w-8 h-8 rounded border-0 bg-transparent p-0 cursor-pointer"><input v-model="settings.welcome.color" type="text" class="w-full bg-transparent outline-none uppercase font-mono text-sm text-white"></div>
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Обычный текст (Вне Embed/V2)</label>
              <textarea v-model="settings.welcome.content" rows="2" placeholder="Эй, {user}, добро пожаловать на {server}!" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-indigo-500 outline-none"></textarea>
            </div>

            <div v-if="settings.welcome.embed_type === 'v1'" class="space-y-4 pt-2 border-t border-gray-800">
              <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Заголовок</label><input v-model="settings.welcome.title" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-indigo-500 outline-none"></div>
              <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Описание</label><textarea v-model="settings.welcome.description" rows="3" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-indigo-500 outline-none"></textarea></div>
              <div class="grid grid-cols-2 gap-4">
                <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Изображение URL</label><input v-model="settings.welcome.image_url" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-indigo-500 outline-none"></div>
                <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Миниатюра URL</label><input v-model="settings.welcome.thumbnail_url" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-indigo-500 outline-none"></div>
              </div>
            </div>

            <div v-if="settings.welcome.embed_type === 'v2'" class="space-y-4 pt-2 border-t border-gray-800">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Блоки Components V2</label>
              <div v-for="(block, index) in settings.welcome.blocks" :key="block.id" class="bg-gray-950 border border-gray-800 p-4 rounded-2xl relative group">
                <div class="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="moveUp('welcome', index)" class="p-1 text-gray-500 hover:text-white"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg></button>
                  <button @click="moveDown('welcome', index)" class="p-1 text-gray-500 hover:text-white"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg></button>
                  <button @click="removeBlock('welcome', index)" class="p-1 text-red-500 hover:text-red-400 ml-1"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
                </div>

                <div v-if="block.type === 'text_display'">
                  <span class="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-2 block">📝 Text Display</span>
                  <textarea v-model="block.content" rows="2" placeholder="Текст (Поддерживает {user}, {server})..." class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-blue-500 outline-none"></textarea>
                </div>
                <div v-else-if="block.type === 'media_gallery'">
                  <span class="text-[10px] font-bold text-green-500 uppercase tracking-widest mb-2 block">🖼️ Media Gallery</span>
                  <input v-model="block.url" type="text" placeholder="URL изображения..." class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-green-500 outline-none mb-2">
                </div>
                <div v-else-if="block.type === 'separator'" class="py-2 text-center text-xs text-gray-600 font-bold tracking-widest">--- РАЗДЕЛИТЕЛЬ ---</div>
                <div v-else-if="block.type === 'section'">
                  <span class="text-[10px] font-bold text-pink-500 uppercase tracking-widest mb-2 block">🔗 Section</span>
                  <input v-model="block.content" type="text" placeholder="Текст слева..." class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none mb-2">
                  <div class="flex gap-2">
                    <input v-model="block.button_label" type="text" placeholder="Текст кнопки" class="w-1/3 bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none">
                    <input v-model="block.button_url" type="text" placeholder="URL ссылки" class="w-2/3 bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none">
                  </div>
                </div>
                <div v-else-if="block.type === 'file'">
                  <span class="text-[10px] font-bold text-yellow-500 uppercase tracking-widest mb-2 block">📎 File</span>
                  <input v-model="block.url" type="text" placeholder="URL файла..." class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-yellow-500 outline-none mb-2">
                </div>
              </div>

              <div class="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
                <button @click="addBlock('welcome', 'text_display')" class="bg-gray-950 border border-gray-800 hover:border-blue-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">📝 Текст</button>
                <button @click="addBlock('welcome', 'media_gallery')" class="bg-gray-950 border border-gray-800 hover:border-green-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">🖼️ Фото</button>
                <button @click="addBlock('welcome', 'section')" class="bg-gray-950 border border-gray-800 hover:border-pink-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">🔗 Секция</button>
                <button @click="addBlock('welcome', 'file')" class="bg-gray-950 border border-gray-800 hover:border-yellow-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">📎 Файл</button>
                <button @click="addBlock('welcome', 'separator')" class="bg-gray-950 border border-gray-800 hover:border-gray-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">➖ Line</button>
              </div>
            </div>
          </div>

          <div class="w-full xl:w-[45%] relative">
            <div class="sticky top-6 flex flex-col gap-4">
              <div class="bg-[#313338] rounded-2xl shadow-2xl overflow-hidden border border-gray-800">
                <div class="bg-[#2b2d31] px-5 py-3 border-b border-[#1e1f22] flex items-center gap-2 text-[#f2f3f5] font-bold text-sm uppercase">
                  <svg class="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg> Предпросмотр
                </div>
                
                <div class="p-5 font-sans text-[15px] text-[#dbdee1] leading-[1.375rem]">
                  <div class="flex gap-4">
                    <img :src="getAvatarUrl(botInfo.id, botInfo.avatar)" class="w-10 h-10 rounded-full mt-0.5 object-cover" />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-baseline gap-1.5 mb-1">
                        <span class="font-medium text-[#f2f3f5]">{{ botInfo.username }}</span>
                        <span class="bg-[#5865F2] text-[10px] px-1.5 py-[1px] rounded text-white font-medium">БОТ</span>
                        <span class="text-xs text-[#80848e] ml-1">{{ currentTime }}</span>
                      </div>
                      
                      <div v-if="settings.welcome.content" class="mb-2 whitespace-pre-wrap break-words" v-html="renderText(settings.welcome.content)"></div>
                      
                      <div v-if="settings.welcome.embed_type === 'v1'" class="flex flex-col relative mt-1 max-w-[520px]">
                        <div class="absolute left-0 top-0 bottom-0 w-1 rounded-l-[4px]" :style="{ backgroundColor: settings.welcome.color || '#5865F2' }"></div>
                        <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-r-[4px] p-4 pl-4 flex gap-4">
                          <div class="flex flex-col min-w-0 flex-1">
                            <div v-if="settings.welcome.title" class="font-bold text-[#f2f3f5] text-base mb-2 break-words" v-html="renderText(settings.welcome.title)"></div>
                            <div v-if="settings.welcome.description" class="whitespace-pre-wrap text-sm mb-3 break-words" v-html="renderText(settings.welcome.description)"></div>
                            <img v-if="settings.welcome.image_url" :src="settings.welcome.image_url" class="rounded max-w-full max-h-[300px] object-cover mb-3" />
                          </div>
                          <div v-if="settings.welcome.thumbnail_url" class="flex-shrink-0 ml-4"><img :src="settings.welcome.thumbnail_url" class="w-20 h-20 rounded object-cover" /></div>
                        </div>
                      </div>

                      <div v-if="settings.welcome.embed_type === 'v2'" class="flex flex-col relative max-w-[520px]">
                        <div class="absolute left-0 top-0 bottom-0 w-1 rounded-[4px]" :style="{ backgroundColor: settings.welcome.color || '#5865F2' }"></div>
                        <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-[4px] py-4 px-4 ml-1 flex flex-col gap-3">
                          <template v-for="(block, idx) in settings.welcome.blocks" :key="block.id">
                            <div v-if="block.type === 'text_display'" class="whitespace-pre-wrap break-words" v-html="renderText(block.content || '')"></div>
                            <div v-else-if="block.type === 'media_gallery'" class="w-full"><img v-if="block.url" :src="block.url" class="rounded-[8px] max-w-full max-h-[300px] object-cover" /></div>
                            <hr v-else-if="block.type === 'separator'" class="border-[#1e1f22] my-1 w-full" />
                            <div v-else-if="block.type === 'section'" class="flex items-center justify-between gap-4">
                              <div class="flex-1 break-words font-medium" v-html="renderText(block.content || '')"></div>
                              <a v-if="block.button_label" :href="block.button_url || '#'" class="flex-shrink-0 bg-[#4e5058] px-4 py-1.5 rounded-[4px] text-white text-sm font-medium">{{ block.button_label }}</a>
                            </div>
                            <div v-else-if="block.type === 'file' && block.url" class="bg-[#2b2d31] border border-[#1e1f22] rounded-[8px] p-3 flex items-center gap-3">
                              <div class="p-2 bg-[#1e1f22] rounded"><svg class="w-6 h-6 text-[#dbdee1]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
                              <div class="flex flex-col"><span class="text-[#00a8fc] text-sm font-medium">{{ block.url.split('/').pop() || 'file' }}</span><span class="text-xs text-[#80848e]">Вложение</span></div>
                            </div>
                          </template>
                          <div class="flex items-center gap-2 mt-2 pt-2 border-t border-[#1e1f22]/50">
                             <span class="text-[11px] text-[#dbdee1] font-medium">Система оповещений • {{ currentTime }}</span>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 rounded-3xl shadow-lg overflow-hidden transition-all" :class="{'ring-2 ring-red-500/50': settings.goodbye.enabled}">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center bg-gray-900/40">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-red-500/20 rounded-xl text-red-400"><svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" /></svg></div>
            <div><h3 class="text-lg font-bold text-white">Выход участника</h3><p class="text-xs text-gray-400">Прощальное сообщение</p></div>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" v-model="settings.goodbye.enabled" class="sr-only peer">
            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-500"></div>
          </label>
        </div>

        <div v-if="settings.goodbye.enabled" class="p-6 animate-fade-in flex flex-col xl:flex-row gap-8">
          
          <div class="w-full xl:w-[55%] space-y-5">
            <div class="flex gap-4">
              <label class="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all" :class="settings.goodbye.embed_type === 'v1' ? 'bg-red-500/10 border-red-500 text-red-400' : 'bg-gray-950 border-gray-700 text-gray-400'">
                <input type="radio" v-model="settings.goodbye.embed_type" value="v1" class="hidden"> Обычный Embed
              </label>
              <label class="flex-1 flex items-center justify-center gap-2 p-3 rounded-xl border cursor-pointer transition-all" :class="settings.goodbye.embed_type === 'v2' ? 'bg-red-500/10 border-red-500 text-red-400' : 'bg-gray-950 border-gray-700 text-gray-400'">
                <input type="radio" v-model="settings.goodbye.embed_type" value="v2" class="hidden"> Components V2
              </label>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Канал</label>
                <select v-model="settings.goodbye.channel_id" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-red-500 outline-none"><option value="" disabled>Выберите канал</option><option v-for="c in channels" :key="c.id" :value="c.id"># {{ c.name }}</option></select>
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Цвет Embed/Контейнера</label>
                <div class="flex items-center gap-2 bg-gray-950 border border-gray-700 px-3 py-1.5 rounded-xl focus-within:border-red-500"><input v-model="settings.goodbye.color" type="color" class="w-8 h-8 rounded border-0 bg-transparent p-0 cursor-pointer"><input v-model="settings.goodbye.color" type="text" class="w-full bg-transparent outline-none uppercase font-mono text-sm text-white"></div>
              </div>
            </div>

            <div>
              <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Обычный текст (Вне Embed/V2)</label>
              <textarea v-model="settings.goodbye.content" rows="2" placeholder="Нас покинул {user}..." class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-red-500 outline-none"></textarea>
            </div>

            <div v-if="settings.goodbye.embed_type === 'v1'" class="space-y-4 pt-2 border-t border-gray-800">
              <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Заголовок</label><input v-model="settings.goodbye.title" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-red-500 outline-none"></div>
              <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Описание</label><textarea v-model="settings.goodbye.description" rows="3" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-3 rounded-xl focus:border-red-500 outline-none"></textarea></div>
              <div class="grid grid-cols-2 gap-4">
                <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Изображение URL</label><input v-model="settings.goodbye.image_url" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-red-500 outline-none"></div>
                <div><label class="block text-xs font-bold text-gray-400 uppercase mb-2">Миниатюра URL</label><input v-model="settings.goodbye.thumbnail_url" type="text" class="w-full bg-gray-950 border border-gray-700 text-white px-4 py-2.5 rounded-xl focus:border-red-500 outline-none"></div>
              </div>
            </div>

            <div v-if="settings.goodbye.embed_type === 'v2'" class="space-y-4 pt-2 border-t border-gray-800">
              <label class="block text-xs font-bold text-gray-400 uppercase mb-2">Блоки Components V2</label>
              <div v-for="(block, index) in settings.goodbye.blocks" :key="block.id" class="bg-gray-950 border border-gray-800 p-4 rounded-2xl relative group">
                <div class="absolute right-2 top-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="moveUp('goodbye', index)" class="p-1 text-gray-500 hover:text-white"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" /></svg></button>
                  <button @click="moveDown('goodbye', index)" class="p-1 text-gray-500 hover:text-white"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" /></svg></button>
                  <button @click="removeBlock('goodbye', index)" class="p-1 text-red-500 hover:text-red-400 ml-1"><svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg></button>
                </div>

                <div v-if="block.type === 'text_display'">
                  <span class="text-[10px] font-bold text-blue-500 uppercase tracking-widest mb-2 block">📝 Text Display</span>
                  <textarea v-model="block.content" rows="2" class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-blue-500 outline-none"></textarea>
                </div>
                <div v-else-if="block.type === 'media_gallery'">
                  <span class="text-[10px] font-bold text-green-500 uppercase tracking-widest mb-2 block">🖼️ Media Gallery</span>
                  <input v-model="block.url" type="text" class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-green-500 outline-none mb-2">
                </div>
                <div v-else-if="block.type === 'separator'" class="py-2 text-center text-xs text-gray-600 font-bold tracking-widest">--- РАЗДЕЛИТЕЛЬ ---</div>
                <div v-else-if="block.type === 'section'">
                  <span class="text-[10px] font-bold text-pink-500 uppercase tracking-widest mb-2 block">🔗 Section</span>
                  <input v-model="block.content" type="text" class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none mb-2">
                  <div class="flex gap-2">
                    <input v-model="block.button_label" type="text" class="w-1/3 bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none">
                    <input v-model="block.button_url" type="text" class="w-2/3 bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-pink-500 outline-none">
                  </div>
                </div>
                <div v-else-if="block.type === 'file'">
                  <span class="text-[10px] font-bold text-yellow-500 uppercase tracking-widest mb-2 block">📎 File</span>
                  <input v-model="block.url" type="text" class="w-full bg-gray-900 border border-gray-800 text-white px-3 py-2 rounded-xl focus:border-yellow-500 outline-none mb-2">
                </div>
              </div>

              <div class="grid grid-cols-2 md:grid-cols-5 gap-2 mt-4">
                <button @click="addBlock('goodbye', 'text_display')" class="bg-gray-950 border border-gray-800 hover:border-blue-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">📝 Текст</button>
                <button @click="addBlock('goodbye', 'media_gallery')" class="bg-gray-950 border border-gray-800 hover:border-green-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">🖼️ Фото</button>
                <button @click="addBlock('goodbye', 'section')" class="bg-gray-950 border border-gray-800 hover:border-pink-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">🔗 Секция</button>
                <button @click="addBlock('goodbye', 'file')" class="bg-gray-950 border border-gray-800 hover:border-yellow-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">📎 Файл</button>
                <button @click="addBlock('goodbye', 'separator')" class="bg-gray-950 border border-gray-800 hover:border-gray-500 text-gray-400 py-2 rounded-xl text-xs font-bold transition-colors">➖ Line</button>
              </div>
            </div>
          </div>

          <div class="w-full xl:w-[45%] relative">
            <div class="sticky top-6 flex flex-col gap-4">
              <div class="bg-[#313338] rounded-2xl shadow-2xl overflow-hidden border border-gray-800">
                <div class="bg-[#2b2d31] px-5 py-3 border-b border-[#1e1f22] flex items-center gap-2 text-[#f2f3f5] font-bold text-sm uppercase">
                  <svg class="w-4 h-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg> Предпросмотр
                </div>
                
                <div class="p-5 font-sans text-[15px] text-[#dbdee1] leading-[1.375rem]">
                  <div class="flex gap-4">
                    <img :src="getAvatarUrl(botInfo.id, botInfo.avatar)" class="w-10 h-10 rounded-full mt-0.5 object-cover" />
                    <div class="flex-1 min-w-0">
                      <div class="flex items-baseline gap-1.5 mb-1">
                        <span class="font-medium text-[#f2f3f5]">{{ botInfo.username }}</span>
                        <span class="bg-[#5865F2] text-[10px] px-1.5 py-[1px] rounded text-white font-medium">БОТ</span>
                        <span class="text-xs text-[#80848e] ml-1">{{ currentTime }}</span>
                      </div>
                      
                      <div v-if="settings.goodbye.content" class="mb-2 whitespace-pre-wrap break-words" v-html="renderText(settings.goodbye.content)"></div>
                      
                      <div v-if="settings.goodbye.embed_type === 'v1'" class="flex flex-col relative mt-1 max-w-[520px]">
                        <div class="absolute left-0 top-0 bottom-0 w-1 rounded-l-[4px]" :style="{ backgroundColor: settings.goodbye.color || '#ED4245' }"></div>
                        <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-r-[4px] p-4 pl-4 flex gap-4">
                          <div class="flex flex-col min-w-0 flex-1">
                            <div v-if="settings.goodbye.title" class="font-bold text-[#f2f3f5] text-base mb-2 break-words" v-html="renderText(settings.goodbye.title)"></div>
                            <div v-if="settings.goodbye.description" class="whitespace-pre-wrap text-sm mb-3 break-words" v-html="renderText(settings.goodbye.description)"></div>
                            <img v-if="settings.goodbye.image_url" :src="settings.goodbye.image_url" class="rounded max-w-full max-h-[300px] object-cover mb-3" />
                          </div>
                          <div v-if="settings.goodbye.thumbnail_url" class="flex-shrink-0 ml-4"><img :src="settings.goodbye.thumbnail_url" class="w-20 h-20 rounded object-cover" /></div>
                        </div>
                      </div>

                      <div v-if="settings.goodbye.embed_type === 'v2'" class="flex flex-col relative max-w-[520px]">
                        <div class="absolute left-0 top-0 bottom-0 w-1 rounded-[4px]" :style="{ backgroundColor: settings.goodbye.color || '#ED4245' }"></div>
                        <div class="bg-[#2b2d31] border border-[#1e1f22] rounded-[4px] py-4 px-4 ml-1 flex flex-col gap-3">
                          <template v-for="(block, idx) in settings.goodbye.blocks" :key="block.id">
                            <div v-if="block.type === 'text_display'" class="whitespace-pre-wrap break-words" v-html="renderText(block.content || '')"></div>
                            <div v-else-if="block.type === 'media_gallery'" class="w-full"><img v-if="block.url" :src="block.url" class="rounded-[8px] max-w-full max-h-[300px] object-cover" /></div>
                            <hr v-else-if="block.type === 'separator'" class="border-[#1e1f22] my-1 w-full" />
                            <div v-else-if="block.type === 'section'" class="flex items-center justify-between gap-4">
                              <div class="flex-1 break-words font-medium" v-html="renderText(block.content || '')"></div>
                              <a v-if="block.button_label" :href="block.button_url || '#'" class="flex-shrink-0 bg-[#4e5058] px-4 py-1.5 rounded-[4px] text-white text-sm font-medium">{{ block.button_label }}</a>
                            </div>
                            <div v-else-if="block.type === 'file' && block.url" class="bg-[#2b2d31] border border-[#1e1f22] rounded-[8px] p-3 flex items-center gap-3">
                              <div class="p-2 bg-[#1e1f22] rounded"><svg class="w-6 h-6 text-[#dbdee1]" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg></div>
                              <div class="flex flex-col"><span class="text-[#00a8fc] text-sm font-medium">{{ block.url.split('/').pop() || 'file' }}</span><span class="text-xs text-[#80848e]">Вложение</span></div>
                            </div>
                          </template>
                          <div class="flex items-center gap-2 mt-2 pt-2 border-t border-[#1e1f22]/50">
                             <span class="text-[11px] text-[#dbdee1] font-medium">Система оповещений • {{ currentTime }}</span>
                          </div>
                        </div>
                      </div>

                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <UnsavedChangesPanel 
          :isDirty="isDirty" 
          :isSaving="isSaving" 
          @reset="resetSettings" 
          @save="saveSettings" 
        />

  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>