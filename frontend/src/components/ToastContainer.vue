<script setup lang="ts">
import { useToast } from '../utils/useToast'
const { toasts } = useToast()
</script>

<template>
  <div class="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none">
    <transition-group name="toast">
      <div v-for="toast in toasts" :key="toast.id" 
           class="flex items-center gap-3 px-5 py-4 rounded-2xl shadow-2xl border backdrop-blur-xl transform transition-all"
           :class="toast.type === 'success' ? 'bg-green-950/80 border-green-500/30 text-green-100 shadow-[0_5px_20px_rgba(34,197,94,0.15)]' : 'bg-red-950/80 border-red-500/30 text-red-100 shadow-[0_5px_20px_rgba(239,68,68,0.15)]'">
        
        <svg v-if="toast.type === 'success'" xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <svg v-else xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        
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