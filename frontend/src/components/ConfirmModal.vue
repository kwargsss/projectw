<script setup lang="ts">
import IconWarning from './icons/IconWarning.vue'
import IconSpinner from './icons/IconSpinner.vue'

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
        <IconWarning class="w-6 h-6 text-yellow-500" />
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
          
          <IconSpinner v-if="isProcessing" class="h-5 w-5 text-white" />
          
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