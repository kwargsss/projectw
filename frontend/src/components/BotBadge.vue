<script setup lang="ts">
import { getAvatarUrl } from '../utils/helpers'

defineProps<{
  botInfo: { id: string | null, username: string, avatar: string | null },
  showSubtitle?: boolean
}>()
</script>

<template>
  <div class="flex items-center gap-4">
    <div class="relative">
      <div class="absolute inset-0 bg-purple-500 rounded-full blur-md opacity-40"></div>
      <img :src="getAvatarUrl(botInfo.id, botInfo.avatar)" alt="Bot Avatar" class="relative w-12 h-12 rounded-full border-2 border-purple-500/50 object-cover shadow-lg transition-all duration-300" />
    </div>
    <div class="flex flex-col">
      <span class="text-xl font-extrabold tracking-tight text-white drop-shadow-md transition-all">{{ botInfo.username }}</span>
      <span v-if="showSubtitle" class="text-xs text-purple-400 font-semibold tracking-wider uppercase mt-0.5">Панель управления</span>
    </div>
  </div>
</template>