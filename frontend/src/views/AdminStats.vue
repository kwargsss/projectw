<script setup lang="ts">
import { inject, computed } from 'vue'

import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line } from 'vue-chartjs'
import IconUserShield from '../components/icons/IconUserShield.vue'
import IconUserGroup from '../components/icons/IconUserGroup.vue'
import IconChartBar from '../components/icons/IconChartBar.vue'
import IconServerBuilding from '../components/icons/IconServerBuilding.vue'
import IconChat from '../components/icons/IconChat.vue'
import IconTerminal from '../components/icons/IconTerminal.vue'
import IconHealth from '../components/icons/IconHealth.vue'
import IconLightning from '../components/icons/IconLightning.vue'
import IconClock from '../components/icons/IconClock.vue'
import IconChip from '../components/icons/IconChip.vue'
import IconCpu from '../components/icons/IconCpu.vue'

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
  <div class="animate-fade-in pb-10">
    <div v-if="botStatus === 'online' && stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-green-500/10 rounded-2xl group-hover:bg-green-500/20 transition-colors">
              <IconServerBuilding class="w-8 h-8 text-green-400" />
            </div>
            <span class="flex h-3 w-3"><span class="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-green-400 opacity-75"></span><span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span></span>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Онлайн сервера</p>
          <h3 class="text-2xl font-bold text-white">{{ stats.online }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-indigo-500/10 rounded-2xl group-hover:bg-indigo-500/20 transition-colors">
              <IconUserGroup class="w-8 h-8 text-indigo-400" />
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Всего участников</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.member_count }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-pink-500/10 rounded-2xl group-hover:bg-pink-500/20 transition-colors">
              <IconChat class="w-8 h-8 text-pink-400" />
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Сообщений (24ч)</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.messages_24h }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-purple-500/10 rounded-2xl group-hover:bg-purple-500/20 transition-colors">
              <IconTerminal class="w-8 h-8 text-purple-400" />
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Команд (24ч)</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.commands_24h }}</h3>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group lg:col-span-2">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 bg-yellow-500/10 rounded-2xl group-hover:bg-yellow-500/20 transition-colors">
              <IconUserShield class="w-8 h-8 text-yellow-400" />
            </div>
          </div>
          <p class="text-gray-400 text-xs font-semibold uppercase tracking-wider mb-1">Администраторов</p>
          <h3 class="text-3xl font-extrabold text-white">{{ stats.admin_count !== undefined ? stats.admin_count : '0' }}</h3>
        </div>
    </div>

    <div v-if="botStatus === 'online' && stats?.health" class="mt-8">
      <div class="flex items-center gap-3 mb-4 px-2">
        <div class="p-2 bg-cyan-500/10 border border-cyan-500/20 rounded-xl">
          <IconHealth class="w-5 h-5 text-cyan-400" />
        </div>
        <h2 class="text-lg font-bold text-white">Здоровье системы (Бот)</h2>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        
        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-4 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group flex flex-col items-start gap-2">
          <div class="p-3 bg-cyan-500/10 rounded-2xl group-hover:bg-cyan-500/20 transition-colors border border-cyan-500/10">
            <IconLightning class="w-6 h-6 text-cyan-400" />
          </div>
          <div>
            <p class="text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-0.5">Ping API</p>
            <h3 class="text-xl font-extrabold text-white flex items-end gap-1">
              {{ stats.health.ping || '0' }} <span class="text-xs font-medium text-gray-400 mb-0.5">мс</span>
            </h3>
          </div>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-4 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group flex flex-col items-start gap-2">
          <div class="p-3 bg-emerald-500/10 rounded-2xl group-hover:bg-emerald-500/20 transition-colors border border-emerald-500/10">
            <IconClock class="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p class="text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-0.5">Время работы</p>
            <h3 class="text-xl font-extrabold text-white">{{ stats.health.uptime || '—' }}</h3>
          </div>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-4 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group flex flex-col items-start gap-2">
          <div class="p-3 bg-orange-500/10 rounded-2xl group-hover:bg-orange-500/20 transition-colors border border-orange-500/10">
            <IconChip class="w-6 h-6 text-orange-400" />
          </div>
          <div>
            <p class="text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-0.5">ОЗУ (Бот)</p>
            <h3 class="text-xl font-extrabold text-white flex items-end gap-1">
              {{ stats.health.ram || '0' }} <span class="text-xs font-medium text-gray-400 mb-0.5">МБ</span>
            </h3>
          </div>
        </div>

        <div class="bg-gray-900/60 backdrop-blur-md border border-gray-800 p-4 rounded-3xl shadow-lg hover:-translate-y-1 transition-all group flex flex-col items-start gap-2">
          <div class="p-3 bg-rose-500/10 rounded-2xl group-hover:bg-rose-500/20 transition-colors border border-rose-500/10">
            <IconCpu class="w-6 h-6 text-rose-400" />
          </div>
          <div>
            <p class="text-gray-400 text-[10px] font-bold uppercase tracking-wider mb-0.5">ЦП (Сист.)</p>
            <h3 class="text-xl font-extrabold text-white flex items-end gap-1">
              {{ stats.health.cpu || '0' }} <span class="text-xs font-medium text-gray-400 mb-0.5">%</span>
            </h3>
          </div>
        </div>
      </div>
    </div>

    <div v-if="botStatus === 'online' && stats?.weekly" class="mt-8 bg-gray-900/60 backdrop-blur-md border border-gray-800 p-6 rounded-3xl shadow-lg transition-all">
      <div class="flex items-center gap-4 mb-6">
        <div class="p-3 bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl">
          <IconChartBar class="w-8 h-8 text-purple-400" />
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