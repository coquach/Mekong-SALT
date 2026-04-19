/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        mekong: {
          navy: "#00203F",
          deep: "#001C1D",
          slate: "#64748B",
          teal: "#006877",
          mint: "#1BAEA6",
          cyan: "#75E7FE",
          critical: "#BA1A1A",
          warning: "#F59E0B",
          optimal: "#2DD4BF",
          info: "#0C355E",
          bg: "#F8FAFC",
        },
      },
      fontFamily: { sans: ['Inter', '"Segoe UI"', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
      boxShadow: { 'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)', 'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.1)' }
    },
  },
  plugins: [],
}
