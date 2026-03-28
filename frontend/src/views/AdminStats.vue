<script setup lang="ts">
import { inject, computed } from 'vue'

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line } from 'vue-chartjs'
import IconUserShield from '../components/icons/IconUserShield.vue'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const botStatus = inject('botStatus') as any
const stats = inject('stats') as any

const chartData = computed(() => {
  if (!stats.value || !stats.value.weekly) return { labels: [], datasets: [] }
  
  const labels = stats.value.weekly.map((day: any) => day.date)
  const messagesData = stats.value.weekly.map((day: any) => day.messages)
  const commandsData = stats.value.weekly.map((day: any) => day.commands)

  return {
    labels,
    datasets: [
      {
        label: 'Сообщения',
        data: messagesData,
        borderColor: '#a855f7',
        backgroundColor: 'rgba(168, 85, 247, 0.15)',
        borderWidth: 3,
        pointBackgroundColor: '#a855f7',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#a855f7',
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Использование команд',
        data: commandsData,
        borderColor: '#ec4899',
        backgroundColor: 'rgba(236, 72, 153, 0.15)',
        borderWidth: 3,
        pointBackgroundColor: '#ec4899',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: '#ec4899',
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.4
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { position: 'top' as const, labels: { color: '#e5e7eb', font: { family: "'Inter', sans-serif", size: 13, weight: 'bold' as const }, usePointStyle: true, boxWidth: 8 } },
    tooltip: { backgroundColor: 'rgba(17, 24, 39, 0.9)', titleColor: '#fff', bodyColor: '#e5e7eb', borderColor: 'rgba(168, 85, 247, 0.3)', borderWidth: 1, padding: 12, cornerRadius: 12, displayColors: true }
  },
  scales: {
    x: { grid: { color: 'rgba(75, 85, 99, 0.2)', drawBorder: false }, ticks: { color: '#9ca3af', font: { family: "'Inter', sans-serif" } } },
    y: { grid: { color: 'rgba(75, 85, 99, 0.2)', drawBorder: false }, ticks: { color: '#9ca3af', font: { family: "'Inter', sans-serif" }, precision: 0 }, beginAtZero: true }
  }
}
</script>

<template>
  <div class="animate-fade-in">
    <div v-if="botStatus === 'online' && stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-green-500/10 rounded-2xl group-hover:bg-green-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-green-400"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 21v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21m0 0h4.5V3.75M5.25 9h3.75m-3.75 3h3.75m-3.75 3h3.75m3.75-6h3.75m-3.75 3h3.75m-3.75 3h3.75" /></svg>
            </div>
            <span class="flex h-3 w-3"><span class="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-green-400 opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span></span>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Онлайн сервера</p>
          <h3 class="text-2xl font-bold text-white">{{ stats.online }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-indigo-500/10 rounded-2xl group-hover:bg-indigo-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-indigo-400"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" /></svg>
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Всего участников</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.member_count }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-pink-500/10 rounded-2xl group-hover:bg-pink-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-pink-400"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.76c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.68-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" /></svg>
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Сообщений (24ч)</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.messages_24h }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-purple-500/10 rounded-2xl group-hover:bg-purple-500/20 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-purple-400"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Команд (24ч)</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.commands_24h }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-yellow-500/10 rounded-2xl group-hover:bg-yellow-500/20 transition-colors">
              <IconUserShield class="w-8 h-8 text-yellow-400" />
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Администраторов</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.admin_count !== undefined ? stats.admin_count : '0' }}</h3>
        </div>
    </div>

    <div v-if="botStatus === 'online' && stats?.weekly" class="mt-8 bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg transition-all">
      <div class="flex items-center gap-4 mb-6">
        <div class="p-3 bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-8 h-8 text-purple-400"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>
        </div>
        <div>
          <h3 class="text-xl font-bold text-white leading-tight">Активность сервера</h3>
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mt-1">График за последние 7 дней</p>
        </div>
      </div>
      
      <div class="w-full h-[22rem] relative mt-2">
        <Line :data="chartData" :options="chartOptions" />
      </div>
    </div>

    <div v-else-if="botStatus === 'offline'" class="bg-red-900/20 border border-red-800/50 p-8 rounded-3xl text-center backdrop-blur-md max-w-2xl mx-auto mt-10">
      <h3 class="text-2xl font-bold text-white mb-2">Бот не в сети</h3>
      <p class="text-gray-400 text-lg">Запустите скрипт бота, чтобы панель получила доступ к статистике.</p>
    </div>
  </div>
</template>

<style scoped>
.animate-fade-in { animation: fadeIn 0.4s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>