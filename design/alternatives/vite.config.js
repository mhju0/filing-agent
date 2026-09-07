import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "node:path";
import { readFileSync } from "node:fs";

export default defineConfig({
  base: "./",
  plugins: [
    {
      name: "inline-theme-before-paint",
      transformIndexHtml: {
        order: "pre",
        handler(html) {
          const theme = readFileSync(
            resolve(import.meta.dirname, "public/theme.js"),
            "utf8",
          );
          return html.replace(
            '<script src="./theme.js"></script>',
            `<script>${theme}</script>`,
          );
        },
      },
    },
    react(),
    tailwindcss(),
  ],
  build: {
    rollupOptions: {
      input: {
        index: resolve(import.meta.dirname, "index.html"),
        a: resolve(import.meta.dirname, "a.html"),
        b: resolve(import.meta.dirname, "b.html"),
        c: resolve(import.meta.dirname, "c.html"),
      },
    },
  },
});
