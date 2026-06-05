/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        mediassist: {
          primary: "#0d9488",
          "primary-hover": "#0f766e",
          "primary-light": "#ccfbf1",
          "primary-muted": "#99f6e4",
          surface: "#ffffff",
          canvas: "#f1f5f9",
          border: "#e2e8f0",
          text: "#0f172a",
          muted: "#64748b",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "Segoe UI", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 3px 0 rgb(0 0 0 / 0.06), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "card-hover": "0 4px 12px 0 rgb(13 148 136 / 0.12)",
      },
    },
  },
  plugins: [],
};
