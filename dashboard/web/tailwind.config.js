/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f0f1a',
        surface: '#1a1a2e',
        'text-primary': '#fafafa',
        'text-muted': '#9ca3af',
        purple: {
          chart: 'oklch(0.488 0.243 264.376)',
        },
        cyan: {
          chart: 'oklch(0.696 0.17 162.48)',
        },
        orange: {
          chart: 'oklch(0.769 0.188 70.08)',
        },
        pink: {
          chart: 'oklch(0.627 0.265 303.9)',
        },
        red: {
          chart: 'oklch(0.645 0.246 16.439)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

