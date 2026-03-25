import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Dashboard from './views/Dashboard.vue'
import AdminStats from './views/AdminStats.vue'
import AdminUsers from './views/AdminUsers.vue'

const routes = [
	{ path: '/', name: 'Home', component: Home },
	{
		path: '/dashboard',
		component: Dashboard,
		children: [
			{ path: '', name: 'AdminStats', component: AdminStats },
			{ path: 'admins', name: 'AdminUsers', component: AdminUsers },
		],
	},
]

const router = createRouter({
	history: createWebHistory(),
	routes,
})

export default router
