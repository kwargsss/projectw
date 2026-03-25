<script setup lang="ts">
import { getAvatarUrl } from '../utils/helpers'

defineProps<{
  user: { id: string, username: string, avatar: string | null, role: string }
}>()

defineEmits(['logout'])
</script>

<template>
  <div class="flex items-center gap-3 bg-gray-900/60 p-1.5 pr-1.5 rounded-full border border-gray-800 backdrop-blur-md shadow-lg">
    <img :src="getAvatarUrl(user.id, user.avatar)" alt="User Avatar" class="w-10 h-10 rounded-full border-2 border-purple-500/40 object-cover" />
    
    <div class="flex flex-col pr-2">
      <span class="text-gray-100 font-bold text-sm leading-tight">{{ user.username }}</span>
      
      <span class="font-medium text-xs leading-tight mt-0.5" 
            :class="{
              'text-purple-400': user.role === 'superadmin',
              'text-blue-400': user.role === 'admin',
              'text-yellow-400': user.role === 'support',
              'text-gray-500': user.role === 'user'
            }">
        {{ 
          user.role === 'superadmin' ? 'Создатель' : 
          user.role === 'admin' ? 'Администратор' : 
          user.role === 'support' ? 'Агент поддержки' : 
          'Пользователь' 
        }}
      </span>
    </div>

    <button @click="$emit('logout')" class="flex items-center justify-center w-9 h-9 rounded-full bg-red-900/30 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors border border-red-500/20" title="Выйти">
      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4 ml-0.5"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" /></svg>
    </button>
  </div>
</template>