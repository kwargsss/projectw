<script setup lang="ts">
import { useToast } from '../utils/useToast'
import IconCheckCircle from './icons/IconCheckCircle.vue'
import IconXCircle from './icons/IconXCircle.vue'

const { toasts } = useToast()
</script>

<template>
  <div class="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
    <transition-group name="toast">
      <div v-for="toast in toasts" :key="toast.id" 
           class="flex items-center gap-3 px-5 py-4 rounded-2xl shadow-2xl border backdrop-blur-xl transform transition-all"
           :class="toast.type === 'success' ? 'bg-green-950/80 border-green-500/30 text-green-100 shadow-[0_5px_20px_rgba(34,197,94,0.15)]' : 'bg-red-950/80 border-red-500/30 text-red-100 shadow-[0_5px_20px_rgba(239,68,68,0.15)]'">
        
        <IconCheckCircle v-if="toast.type === 'success'" class="w-6 h-6 text-green-400" />
        <IconXCircle v-else class="w-6 h-6 text-red-400" />
        
        <span class="font-bold text-sm tracking-wide">{{ toast.text }}</span>
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
.toast-enter-from { opacity: 0; transform: translateX(50px) scale(0.9); }
.toast-leave-to { opacity: 0; transform: translateX(50px) scale(0.9); }
</style>