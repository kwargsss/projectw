import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/',
		name: 'Home',
		component: () => import('./views/Home.vue'),
	},
	{
		path: '/dashboard',
		component: () => import('./views/Dashboard.vue'),
		children: [
			{
				path: '',
				name: 'AdminStats',
				component: () => import('./views/AdminStats.vue'),
			},
			{
				path: 'admins',
				name: 'AdminUsers',
				component: () => import('./views/AdminUsers.vue'),
			},
			{
				path: 'embed',
				name: 'EmbedBuilder',
				component: () => import('./views/EmbedBuilder.vue'),
			},
			{
				path: 'embed_v2',
				name: 'EmbedBuilderV2',
				component: () => import('./views/EmbedBuilderV2.vue'),
			},
			{
				path: 'notifications',
				name: 'Notifications',
				component: () => import('./views/Notifications.vue'),
			},
			{
				path: 'tickets',
				name: 'Tickets',
				component: () => import('./views/Tickets.vue'),
			},
			{
				path: 'tickets/:type/:id',
				name: 'TicketChat',
				component: () => import('./views/TicketChat.vue'),
			},
		],
	},
]

const router = createRouter({
	history: createWebHistory(),
	routes,
})

export default router
