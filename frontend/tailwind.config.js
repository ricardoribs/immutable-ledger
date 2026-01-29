/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: '#1b3f2a',
          primary: '#2f6b45',
          accent: '#8bdc63',
          light: '#f6f4ef',
          danger: '#ef4444',
          ink: '#0e1511',
        }
      },
      fontFamily: {
        sans: ['Manrope', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}

