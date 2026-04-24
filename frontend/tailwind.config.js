/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        dark: {
          900: '#030712',
          800: '#0a0f1a',
          700: '#111827',
          600: '#1f2937',
          500: '#374151',
        },
      },
    },
  },
  plugins: [],
}
