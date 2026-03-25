<script setup lang="ts">
defineProps<{
  isOpen: boolean
  isProcessing?: boolean
  title?: string
  confirmText?: string
  cancelText?: string
  type?: 'primary' | 'danger'
}>()

defineEmits(['confirm', 'cancel'])
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm px-4 animate-fade-in">
    <div class="bg-gray-900 border border-gray-800 rounded-3xl p-7 max-w-sm w-full shadow-2xl transform transition-all scale-100">
      
      <h3 class="text-xl font-extrabold text-white mb-3 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-6 h-6 text-yellow-500">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        {{ title || 'Подтверждение' }}
      </h3>
      
      <div class="text-gray-300 mb-8 leading-relaxed">
        <slot></slot>
      </div>
      
      <div class="flex justify-end gap-3">
        <button @click="$emit('cancel')" :disabled="isProcessing" 
                class="px-5 py-2.5 rounded-xl font-bold text-gray-400 hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          {{ cancelText || 'Отмена' }}
        </button>
        
        <button @click="$emit('confirm')" :disabled="isProcessing" 
                class="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-white transition-all shadow-lg disabled:opacity-75 disabled:cursor-wait"
                :class="type === 'danger' ? 'bg-red-600 hover:bg-red-500 shadow-red-500/20' : 'bg-purple-600 hover:bg-purple-500 shadow-purple-500/20'">
          
          <svg v-if="isProcessing" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          
          <span v-if="!isProcessing">{{ confirmText || 'Да, уверен' }}</span>
          <span v-else>Обработка...</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.2s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
</style>