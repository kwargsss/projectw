import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from './composables/useAuth'

const routes = [
	{
		path: '/',
		name: 'Home',
		component: () => import('./views/Home.vue'),
	},
	{
		path: '/profile/:id',
		name: 'UserDashboard',
		component: () => import('./views/UserDashboard.vue'),
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

router.beforeEach(async (to, from, next) => {
	const { user, isLoggedIn, fetchUser } = useAuth()
	const allowedAdminRoles = ['admin', 'superadmin', 'support']

	if (to.path.startsWith('/dashboard')) {
		await fetchUser()

		if (!isLoggedIn.value || !user.value) {
			return next('/')
		}

		if (!allowedAdminRoles.includes(user.value.role)) {
			return next(`/profile/${user.value.id}`)
		}
	}

	if (to.name === 'UserDashboard') {
		await fetchUser()

		if (!isLoggedIn.value || !user.value) {
			return next('/')
		}

		const isOwner = user.value.id === to.params.id
		const isAdmin = allowedAdminRoles.includes(user.value.role)

		if (!isOwner && !isAdmin) {
			return next(`/profile/${user.value.id}`)
		}
	}

	next()
})

export default router
