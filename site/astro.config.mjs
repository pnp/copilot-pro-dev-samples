// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

// https://astro.build/config
export default defineConfig({
	base: process.env.GITHUB_ACTIONS === "true" ? "/copilot-pro-dev-samples" : "/",
	vite: {
		plugins: [tailwindcss()],
	},
});
