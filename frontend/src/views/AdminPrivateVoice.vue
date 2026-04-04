<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '../utils/useToast'
import IconServerBuilding from '../components/icons/IconServerBuilding.vue'
import ConfirmModal from '../components/ConfirmModal.vue'
import IconTrash from '../components/icons/IconTrash.vue'

const { showToast } = useToast()
const API_URL = import.meta.env.VITE_API_BASE_URL
const guildId = import.meta.env.VITE_DISCORD_GUILD_ID

const isLoading = ref(true)
const isSaving = ref(false)
const isDeploying = ref(false)

const isDeployModalOpen = ref(false)
const isRedeployModalOpen = ref(false)
const isDeleteModalOpen = ref(false)
const isDisableModalOpen = ref(false)

const config = ref({
  is_enabled: false,
  template: '🎧 {nick}',
  default_limit: 0,
  default_bitrate: 64000,
  is_deployed: false
})

const fetchConfig = async () => {
  try {
    const res = await fetch(`${API_URL}/private-voice/${guildId}`)
    const data = await res.json()
    if (data.status === 'ok') {
      config.value = data.data
    }
  } catch (e) {
    showToast('Ошибка загрузки настроек', 'error')
  } finally {
    isLoading.value = false
  }
}

const saveConfig = async (silent = false) => {
  isSaving.value = true
  try {
    const res = await fetch(`${API_URL}/private-voice/${guildId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    })
    if (res.ok && !silent) showToast('Настройки сохранены', 'success')
  } catch (e) {
    showToast('Ошибка сохранения', 'error')
  } finally {
    isSaving.value = false
  }
}

// Обработчик кнопки развертывания
const requestDeploy = () => {
  if (config.value.is_deployed) {
    isRedeployModalOpen.value = true
  } else {
    isDeployModalOpen.value = true
  }
}

// Сам процесс развертывания
const executeDeploy = async () => {
  isDeploying.value = true
  try {
    const res = await fetch(`${API_URL}/private-voice/${guildId}/deploy`, { method: 'POST' })
    if (res.ok) {
      showToast('Установка запущена! Проверьте Discord.', 'success')
      config.value.is_deployed = true
      config.value.is_enabled = true
      await saveConfig(true)
      
      // Даем боту время 3 секунды, чтобы он точно создал каналы, и обновляем статус
      setTimeout(() => fetchConfig(), 3000) 
    }
  } catch (e) {
    showToast('Ошибка развертывания', 'error')
  } finally {
    isDeploying.value = false
    isDeployModalOpen.value = false
    isRedeployModalOpen.value = false
  }
}

// Обработчик ползунка Вкл/Выкл
const handleToggleClick = (e: Event) => {
  e.preventDefault()
  if (config.value.is_enabled) {
    isDisableModalOpen.value = true // Запрашиваем подтверждение выключения
  } else {
    config.value.is_enabled = true
    saveConfig()
  }
}

const confirmDisable = async () => {
  config.value.is_enabled = false
  await saveConfig()
  isDisableModalOpen.value = false
}

// Полное удаление системы
const confirmDeleteSetup = async () => {
  isSaving.value = true
  try {
    const res = await fetch(`${API_URL}/private-voice/${guildId}/undeploy`, { method: 'POST' })
    if (res.ok) {
      showToast('Система полностью удалена с сервера', 'success')
      config.value.is_deployed = false
      config.value.is_enabled = false
    }
  } catch (e) {
    showToast('Ошибка удаления', 'error')
  } finally {
    isSaving.value = false
    isDeleteModalOpen.value = false
  }
}

onMounted(() => fetchConfig())
</script>

<template>
  <div class="animate-fade-in relative z-10">
    <div class="mb-8">
      <h2 class="text-3xl font-extrabold text-white flex items-center gap-3">
        <span class="p-2.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400">
          <IconServerBuilding class="w-7 h-7" />
        </span>
        Приватные комнаты
      </h2>
      <p class="text-gray-400 mt-2 font-medium">Мощная система автоматических голосовых каналов для вашего сервера.</p>
    </div>

    <div v-if="isLoading" class="flex justify-center py-12">
      <div class="w-10 h-10 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
    </div>

    <div v-else-if="!config.is_deployed" class="bg-gray-900/60 border border-gray-800/80 rounded-3xl p-10 shadow-lg text-center max-w-3xl mx-auto mt-10">
      <div class="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-blue-500/20">
        <IconServerBuilding class="w-10 h-10 text-blue-400" />
      </div>
      <h3 class="text-2xl font-bold text-white mb-4">Система не установлена</h3>
      <p class="text-gray-400 mb-8 text-lg">
        Нажмите кнопку ниже, чтобы бот автоматически создал категорию «Приватные каналы», текстовый пульт управления и голосовой канал для создания комнат.
      </p>
      
      <button @click="requestDeploy" class="bg-blue-600 hover:bg-blue-500 px-8 py-4 rounded-2xl font-bold transition-all text-white text-lg shadow-[0_0_30px_rgba(59,130,246,0.3)] flex justify-center items-center gap-3 mx-auto">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
        Развернуть систему на сервере
      </button>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-gray-900/60 border border-gray-800/80 rounded-3xl p-6 shadow-lg">
          
          <div class="flex items-center justify-between mb-6 pb-6 border-b border-gray-800">
            <div>
              <h3 class="text-xl font-bold text-white">Статус работы</h3>
              <p class="text-sm text-gray-500">Временно отключить создание комнат (каналы не удалятся)</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" :checked="config.is_enabled" @click="handleToggleClick" class="sr-only peer">
              <div class="w-14 h-7 bg-gray-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-gray-400 peer-checked:after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-blue-500"></div>
            </label>
          </div>

          <div class="space-y-6">
            <div>
              <label class="block text-sm font-bold text-gray-300 mb-1.5">Шаблон названия комнаты</label>
              <input v-model="config.template" type="text" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors">
              <div class="mt-2 flex flex-wrap gap-2 text-xs">
                <span class="bg-gray-800 text-gray-300 px-2 py-1 rounded"><b>{nick}</b> - Ник на сервере</span>
                <span class="bg-gray-800 text-gray-300 px-2 py-1 rounded"><b>{user}</b> - Логин Discord</span>
                <span class="bg-gray-800 text-gray-300 px-2 py-1 rounded"><b>{game}</b> - Текущая игра</span>
                <span class="bg-gray-800 text-gray-300 px-2 py-1 rounded"><b>{server}</b> - Имя сервера</span>
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-bold text-gray-300 mb-1.5">Лимит (по умолч.)</label>
                <input v-model="config.default_limit" type="number" min="0" max="99" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors">
                <p class="text-xs text-gray-500 mt-1.5">0 = без лимита</p>
              </div>
              <div>
                <label class="block text-sm font-bold text-gray-300 mb-1.5">Битрейт (по умолч.)</label>
                <select v-model="config.default_bitrate" class="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:outline-none transition-colors">
                  <option :value="32000">32 kbps</option>
                  <option :value="64000">64 kbps</option>
                  <option :value="96000">96 kbps</option>
                  <option :value="128000">128 kbps</option>
                </select>
              </div>
            </div>
            
            <div class="pt-2 flex justify-end">
              <button @click="saveConfig(false)" :disabled="isSaving" class="bg-blue-600 hover:bg-blue-500 px-6 py-2.5 rounded-xl font-bold transition-colors text-white disabled:opacity-50">
                {{ isSaving ? 'Сохранение...' : 'Сохранить настройки' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-red-900/10 border border-red-500/20 rounded-3xl p-6 shadow-lg">
          <h3 class="text-xl font-bold text-red-400 mb-2">Опасная зона</h3>
          <p class="text-sm text-gray-400 mb-6">
            Полное удаление категории «Приватные каналы», панели управления и всех активных комнат с сервера.
          </p>
          
          <button @click="isDeleteModalOpen = true" class="w-full bg-red-600/10 hover:bg-red-600/20 text-red-500 border border-red-500/30 py-3 rounded-xl font-bold transition-colors flex justify-center items-center gap-2">
            <IconTrash class="w-5 h-5" />
            Удалить систему с сервера
          </button>
        </div>
      </div>
    </div>

    <ConfirmModal :isOpen="isDeployModalOpen" :isProcessing="isDeploying" type="warning" title="Установка системы" confirmText="Развернуть" cancelText="Отмена" @confirm="executeDeploy" @cancel="isDeployModalOpen = false">
      Бот создаст новую категорию <b>«🔒 Приватные каналы»</b> на вашем сервере. Вы уверены?
    </ConfirmModal>

    <ConfirmModal :isOpen="isRedeployModalOpen" :isProcessing="isDeploying" type="warning" title="Повторное развертывание" confirmText="Создать каналы" cancelText="Отмена" @confirm="executeDeploy" @cancel="isRedeployModalOpen = false">
      Система уже развернута. Точно создать <b>ЕЩЕ ОДНУ</b> категорию и каналы?
    </ConfirmModal>

    <ConfirmModal :isOpen="isDisableModalOpen" :isProcessing="false" type="danger" title="Отключение модуля" confirmText="Выключить" cancelText="Отмена" @confirm="confirmDisable" @cancel="isDisableModalOpen = false">
      Вы хотите выключить создание новых комнат? (Уже созданные комнаты не удалятся).
    </ConfirmModal>

    <ConfirmModal :isOpen="isDeleteModalOpen" :isProcessing="isSaving" type="danger" title="Снос системы" confirmText="Да, удалить всё" cancelText="Отмена" @confirm="confirmDeleteSetup" @cancel="isDeleteModalOpen = false">
      Вы собираетесь <b>полностью удалить</b> категорию приватных каналов и пульт управления. Текущие комнаты пользователей также могут быть удалены. Продолжить?
    </ConfirmModal>

  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
</style>