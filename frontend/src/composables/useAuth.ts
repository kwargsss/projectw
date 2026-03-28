import { ref } from 'vue'

const API_URL = import.meta.env.VITE_API_BASE_URL

export interface User {
	id: string
	username: string
	avatar: string | null
	role: string
}

export function useAuth() {
	const user = ref<User | null>(null)
	const isLoggedIn = ref(false)
	const error = ref<string | null>(null)

	const fetchUser = async () => {
		try {
			const res = await fetch(`${API_URL}/auth/me`, { credentials: 'include' })
			if (res.ok) {
				user.value = await res.json()
				isLoggedIn.value = true
			} else {
				isLoggedIn.value = false
				user.value = null
			}
		} catch (err) {
			isLoggedIn.value = false
			user.value = null
		}
	}

	const login = async () => {
		try {
			const response = await fetch(`${API_URL}/auth/login`)
			const data = await response.json()
			if (data.url) window.location.href = data.url
		} catch (err) {
			error.value = 'Сервер недоступен.'
		}
	}

	const logout = async () => {
		try {
			await fetch(`${API_URL}/auth/logout`, {
				method: 'POST',
				credentials: 'include',
			})
		} finally {
			isLoggedIn.value = false
			user.value = null
		}
	}

	return { user, isLoggedIn, error, fetchUser, login, logout }
}
