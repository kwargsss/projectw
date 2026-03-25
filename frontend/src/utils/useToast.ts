import { ref } from 'vue'

export type ToastType = 'success' | 'error'

export interface Toast {
	id: number
	text: string
	type: ToastType
}

const toasts = ref<Toast[]>([])
let toastId = 0

export const useToast = () => {
	const showToast = (
		text: string,
		type: ToastType = 'success',
		duration = 3000,
	) => {
		const id = toastId++
		toasts.value.push({ id, text, type })

		setTimeout(() => {
			toasts.value = toasts.value.filter(t => t.id !== id)
		}, duration)
	}

	return {
		toasts,
		showToast,
	}
}
