import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./app/**/*.{js,ts,jsx,tsx}",
  ],
  safelist: [
    'text-rb-gold',
    'bg-rb-gold',
    'border-rb-gold',
    'text-rb-yellow',
    'bg-rb-yellow',
  ],
  theme: {
    extend: {
      colors: {
        "rb-brand-navy": "#142855",
        "rb-navy": "#142855",
        "rb-navy-deep": "#121F45",
        "rb-blue": "#223971",
        "rb-red": "#CC1E4A",
        "rb-gold": "#FFC906",
        "rb-yellow": "#FFC906",
        "rb-white": "#FFFFFF",
        "rb-grey": "#9CA3AF",
        "rb-black": "#111827",
        "rb-border": "#E5E7EB",
        "rb-row-hover": "#F3F4F6",
        "rb-canvas": "#0E1117",
        "rb-grid": "#2B2F36",
        "rb-axis": "#B2B9C3",
        "rb-anno": "#707C91",
        "rb-dem": "#5B8AEF",
        "rb-gop": "#E06A6A",
        "rb-ind": "#F4B400",
        "rb-up": "#21C36F",
        "rb-down": "#E94C49",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ['"Libre Baskerville"', "serif"],
      },
      boxShadow: {
        "card-glow": "0 10px 50px rgba(18, 31, 69, 0.45)",
        "gold-glow": "0 0 6px rgba(255, 201, 6, 0.5)",
      },
      borderRadius: {
        xl: "18px",
      },
    },
  },
  plugins: [],
};

export default config;
