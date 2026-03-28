import { ref } from 'vue'

const API_URL = import.meta.env.VITE_API_BASE_URL

export interface BotInfo {
	id: string | null
	username: string
	avatar: string | null
}

export function useBot() {
	const botInfo = ref<BotInfo>({
		id: null,
		username: 'Загрузка...',
		avatar: null,
	})

	const fetchBot = async () => {
		try {
			const botRes = await fetch(`${API_URL}/bot`)
			if (botRes.ok) {
				const data = await botRes.json()
				botInfo.value = data.data
			}
		} catch (e) {
			console.error('Failed to fetch bot info', e)
		}
	}

	return { botInfo, fetchBot }
}
