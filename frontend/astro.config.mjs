// @ts-check
import { defineConfig } from 'astro/config';
import vercel from '@astrojs/vercel/serverless';
import react from '@astrojs/react';
import clerk from "@clerk/astro";

// https://astro.build/config
export default defineConfig({
  integrations: [react(), clerk()],
  adapter: vercel(),
  output: 'server'
});