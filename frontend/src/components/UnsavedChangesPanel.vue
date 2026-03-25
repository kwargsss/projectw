<script setup lang="ts">
defineProps<{
  isDirty: boolean;
  isSaving: boolean;
}>()

defineEmits<{
  (e: 'reset'): void;
  (e: 'save'): void;
}>()
</script>

<template>
  <transition name="slide-up">
    <div v-if="isDirty" class="fixed bottom-6 left-1/2 -translate-x-1/2 w-auto min-w-[400px] bg-gray-900/95 backdrop-blur-xl border border-gray-700 p-3 pl-5 rounded-2xl shadow-2xl flex items-center justify-between gap-6 z-50">
      <span class="text-white text-sm font-medium">У вас есть несохраненные изменения!</span>
      
      <div class="flex items-center gap-2">
        <button @click="$emit('reset')" class="px-3 py-1.5 text-gray-400 hover:text-white text-sm font-medium transition-colors">
          Сбросить
        </button>
        
        <button @click="$emit('save')" :disabled="isSaving" class="bg-green-600 hover:bg-green-500 text-white px-4 py-1.5 rounded-lg text-sm font-bold transition-all shadow-[0_0_15px_rgba(22,163,74,0.4)] flex items-center gap-2">
          <svg v-if="isSaving" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span v-else>Сохранить</span>
        </button>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translate(-50%, 100%); }
.slide-up-enter-to, .slide-up-leave-from { opacity: 1; transform: translate(-50%, 0); }
</style>