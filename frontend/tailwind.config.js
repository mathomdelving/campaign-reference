/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'bg-rb-navy',
    'bg-rb-blue',
    'bg-rb-red',
    'bg-rb-yellow',
    'text-rb-navy',
    'text-rb-blue',
    'text-rb-red',
    'text-rb-yellow',
    'border-rb-navy',
    'border-rb-blue',
    'border-rb-red',
    'border-rb-yellow',
    'hover:bg-rb-navy',
    'hover:bg-rb-blue',
    'hover:bg-rb-red',
    'hover:text-rb-blue',
    'hover:text-rb-red',
    'focus:ring-rb-red',
  ],
  theme: {
    extend: {
      colors: {
        'rb-navy': '#121F45',
        'rb-blue': '#223971',
        'rb-red': '#CC1E4A',
        'rb-yellow': '#FFC906',
      },
    },
  },
  plugins: [],
}