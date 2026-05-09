/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        neon: '#22c55e',
        'neon-dark': '#16a34a',
        'dark': '#0a0f1a',
        'dark-2': '#0d1526',
        'dark-3': '#111827',
        'dark-card': '#1a2236',
        'dark-border': '#1e2d3d',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'neon': '0 0 20px rgba(34, 197, 94, 0.3)',
        'neon-lg': '0 0 40px rgba(34, 197, 94, 0.2)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}
