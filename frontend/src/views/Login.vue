<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const error = ref<string | null>(null)

const API_URL = import.meta.env.VITE_API_BASE_URL

onMounted(async () => {
  if (route.query.error) {
    error.value = "Ошибка авторизации. Попробуйте еще раз."
  }

  try {
    const res = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
    if (res.ok) {
      router.push('/dashboard')
    }
  } catch (err) {
  }
})

const login = async () => {
  try {
    const response = await fetch(`${API_URL}/auth/login`)
    const data = await response.json()
    if (data.url) window.location.href = data.url
  } catch (err) {
    error.value = "Сервер недоступен."
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-950 flex flex-col items-center justify-center p-4">
    <div class="bg-gray-900 border border-gray-800 p-10 rounded-3xl shadow-2xl max-w-md w-full text-center">
      <div class="flex justify-center mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-16 h-16 text-purple-500">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 8.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25a2.25 2.25 0 0 1-2.25 2.25h-2.25A2.25 2.25 0 0 1 13.5 8.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
        </svg>
      </div>
      <h1 class="text-3xl font-extrabold text-white mb-2">Bot<span class="text-purple-500">Panel</span></h1>
      <p class="text-gray-400 mb-8">Войдите, чтобы получить доступ к панели управления.</p>

      <div v-if="error" class="mb-4 text-red-400 bg-red-900/30 p-3 rounded-lg text-sm border border-red-800">
        {{ error }}
      </div>

      <button @click="login" class="w-full flex items-center justify-center gap-3 bg-purple-600 hover:bg-purple-700 text-white px-6 py-3.5 rounded-xl font-semibold transition-all shadow-lg hover:shadow-purple-500/20">
        <svg class="w-5 h-5 fill-white" viewBox="0 0 640 512" xmlns="http://www.w3.org/2000/svg"><path d="M524.531 69.836a1.5 1.5 0 0 0-.764-.7A485.065 485.065 0 0 0 404.081 32.03a1.816 1.816 0 0 0-1.923.91 337.461 337.461 0 0 0-14.9 30.6 447.848 447.848 0 0 0-134.426 0 309.541 309.541 0 0 0-15.135-30.6 1.89 1.89 0 0 0-1.924-.91 483.689 483.689 0 0 0-119.688 37.107 1.712 1.712 0 0 0-.788.676C39.068 183.651 18.186 294.69 28.43 404.354a2.016 2.016 0 0 0 .765 1.375 487.666 487.666 0 0 0 146.825 74.189 1.9 1.9 0 0 0 2.063-.676A348.2 348.2 0 0 0 208.12 430.4a1.86 1.86 0 0 0-1.019-2.588 321.173 321.173 0 0 1-45.868-21.853 1.885 1.885 0 0 1-.185-3.126 245.576 245.576 0 0 0 9.109-7.137 1.819 1.819 0 0 1 1.9-.256c96.229 43.917 200.41 43.917 295.5 0a1.812 1.812 0 0 1 1.924.233 234.533 234.533 0 0 0 9.132 7.16 1.884 1.884 0 0 1-.162 3.126 301.407 301.407 0 0 1-45.89 21.83 1.875 1.875 0 0 0-1.011 2.61 381.19 381.19 0 0 0 29.89 49.362 1.916 1.916 0 0 0 2.107.7 486.582 486.582 0 0 0 146.97-74.204 1.871 1.871 0 0 0 .774-1.351c12.198-121.152-19.177-231.066-82.903-334.331zM222.791 337.58c-28.972 0-52.844-26.587-52.844-59.239s23.409-59.241 52.844-59.241c29.665 0 53.306 26.589 52.843 59.241.013 32.654-23.41 59.239-52.843 59.239zm195.38 0c-28.971 0-52.843-26.587-52.843-59.239s23.409-59.241 52.843-59.241c29.667 0 53.307 26.589 52.844 59.241s-23.177 59.239-52.844 59.239z"/></svg>
        Войти через Discord
      </button>
    </div>
  </div>
</template>