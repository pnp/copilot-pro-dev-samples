// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
	site: "https://pnp.github.io",
	base: process.env.GITHUB_ACTIONS === "true" ? "/copilot-pro-dev-samples" : "/",
	trailingSlash: "always",
});
