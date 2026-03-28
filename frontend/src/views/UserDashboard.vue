<script setup lang="ts">
import IconStar from '../components/icons/IconStar.vue'

defineProps<{ user: any }>()
</script>

<template>
  <div class="bg-gray-900/40 backdrop-blur-md border border-gray-800 p-12 rounded-3xl shadow-lg text-center max-w-3xl mx-auto mt-10">
    <div class="bg-purple-900/30 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 border border-purple-500/30">
      <IconStar class="w-12 h-12 text-purple-400" />
    </div>
    <h2 class="text-3xl font-bold text-white mb-4">Раздел в разработке</h2>
    <p class="text-gray-400 text-lg">Скоро здесь появится система лидербордов, экономика и ваша личная статистика на сервере. Следите за обновлениями!</p>
  </div>
</template>