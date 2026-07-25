/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        toss_black: '#121212',
        toss_navy: '#1A1A2E',
        toss_text_primary: '#E0E0E0',
        toss_text_secondary: '#A0A0A0',
        toss_blue: '#3182F6',
        toss_red: '#EF4444',
      },
      fontFamily: {
        sans: ['Pretendard', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
