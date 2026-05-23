/** @type {import('tailwindcss').Config} */
const { fontFamily } = require('tailwindcss/defaultTheme');

module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Fredoka', ...fontFamily.sans],
        comic: ['"Comic Neue"', 'cursive'],
      },
      colors: {
        primary: {
          DEFAULT: '#BD93F9',   // Dracula Purple
          light: '#D6BCFA',
          dark: '#8A63D2',
        },
        secondary: {
          DEFAULT: '#FF79C6',   // Dracula Pink
          light: '#FFB6E6',
          dark: '#CC6699',
        },
        accent: {
          DEFAULT: '#8BE9FD',   // Dracula Cyan
          light: '#C0F7FE',
          dark: '#4CD6E6',
        },
        warning: {
          DEFAULT: '#FFB86C',   // Dracula Orange
          light: '#FFD6A0',
          dark: '#FF8800',
        },
        success: {
          DEFAULT: '#50FA7B',   // Dracula Green
          light: '#A8FFC6',
          dark: '#1FC66E',
        },
        danger: {
          DEFAULT: '#FF5555',   // Dracula Red
          light: '#FF9999',
          dark: '#D62828',
        },
        neutral: {
          light: '#F8F8F2',     // Dracula White
          DEFAULT: '#6272A4',   // Muted Blue
          dark: '#44475A',      // Dracula Surface
        },
        background: {
          DEFAULT: '#282A36',   // Dracula Background
          soft: '#1E1F29',      // Slightly darker
          paper: '#44475A',     // Surface/Card
        },
        text: {
          base: '#F8F8F2',      // Dracula White
          muted: '#6272A4',
          inverted: '#1E1F29',
        },
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(180deg, #282A36 0%, #1E1F29 100%)',
      },
      borderRadius: {
        'xl': '1.5rem',
        '2xl': '2rem',
      },
      boxShadow: {
        card: '0 4px 12px rgba(0, 0, 0, 0.08)',
        'card-hover': '0 8px 24px rgba(0, 0, 0, 0.12)',
        elevated: '0 12px 24px rgba(0, 0, 0, 0.16)',
        glow: '0 0 8px rgba(139, 233, 253, 0.7)', // Cyan Glow
      },
      keyframes: {
        'spin-once': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        'bounce-once': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-15%)' },
        },
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'scale-up': {
          from: { transform: 'scale(0.96)', opacity: '0' },
          to: { transform: 'scale(1)', opacity: '1' },
        },
        'slide-in-left': {
          from: { transform: 'translateX(-20%)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'flip': {
          from: { transform: 'rotateY(90deg)', opacity: '0' },
          to: { transform: 'rotateY(0deg)', opacity: '1' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.85 },
        },
      },
      animation: {
        'spin-once': 'spin-once 0.8s ease-out forwards',
        'bounce-once': 'bounce-once 0.6s ease-out forwards',
        'fade-in': 'fade-in 0.5s ease-out forwards',
        'scale-up': 'scale-up 0.4s ease-out forwards',
        'slide-in-left': 'slide-in-left 0.6s ease-out forwards',
        'flip': 'flip 0.5s ease-out forwards',
        'pulse-soft': 'pulse-soft 1.5s ease-in-out infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
