import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Dashboard from './views/Dashboard.vue'
import AdminStats from './views/AdminStats.vue'
import AdminUsers from './views/AdminUsers.vue'
import EmbedBuilder from './views/EmbedBuilder.vue'
import EmbedBuilderV2 from './views/EmbedBuilderV2.vue'
import Notifications from './views/Notifications.vue'
import Tickets from './views/Tickets.vue'

const routes = [
	{ path: '/', name: 'Home', component: Home },
	{
		path: '/dashboard',
		component: Dashboard,
		children: [
			{ 
				path: '', 
				name: 'AdminStats', 
				component: AdminStats 
			},
			{ 
				path: 'admins', 
				name: 'AdminUsers', 
				component: AdminUsers 
			},
			{ 
				path: 'embed', 
				name: 'EmbedBuilder', 
				component: EmbedBuilder 
			},
			{ 
				path: 'embed_v2', 
				name: 'EmbedBuilderV2', 
				component: EmbedBuilderV2 
			},
			{
				path: 'notifications',
				name: 'Notifications',
				component: Notifications,
			},
			{ 
				path: 'tickets',
				name: 'Tickets', 
				component: Tickets 
			},
		],
	},
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
