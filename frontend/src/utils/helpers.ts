export const getAvatarUrl = (
	id: string | null,
	hash: string | null,
	size = 128,
): string => {
	if (id && hash) {
		return `https://cdn.discordapp.com/avatars/${id}/${hash}.png?size=${size}`
	}
	return `https://cdn.discordapp.com/embed/avatars/0.png`
}
