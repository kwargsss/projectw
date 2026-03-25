<script setup lang="ts">
defineProps<{ user: any }>()
</script>

<template>
  <div class="bg-gray-900/40 backdrop-blur-md border border-gray-800 p-12 rounded-3xl shadow-lg text-center max-w-3xl mx-auto mt-10">
    <div class="bg-purple-900/30 w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-6 border border-purple-500/30">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-12 h-12 text-purple-400"><path stroke-linecap="round" stroke-linejoin="round" d="M11.48 3.499a.562.562 0 0 1 1.04 0l2.125 5.111a.563.563 0 0 0 .475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 0 0-.182.557l1.285 5.385a.562.562 0 0 1-.84.61l-4.725-2.885a.562.562 0 0 0-.586 0L6.982 20.54a.562.562 0 0 1-.84-.61l1.285-5.386a.562.562 0 0 0-.182-.557l-4.204-3.602a.562.562 0 0 1 .321-.988l5.518-.442a.563.563 0 0 0 .475-.345L11.48 3.5Z" /></svg>
    </div>
    <h2 class="text-3xl font-bold text-white mb-4">Раздел в разработке</h2>
    <p class="text-gray-400 text-lg">Скоро здесь появится система лидербордов, экономика и ваша личная статистика на сервере. Следите за обновлениями!</p>
  </div>
</template>