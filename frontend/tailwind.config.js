/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#080c14",
        panel: "#101826",
        raised: "#162033",
        line: "#243044",
        mist: "#8b98b3",
        snow: "#e8eef8",
        accent: "#3ecfc4",
        warn: "#d4a84b",
        danger: "#e05d6a",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(255,255,255,0.03), 0 12px 32px rgba(0,0,0,0.28)",
      },
      keyframes: {
        enter: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
      },
      animation: {
        enter: "enter 0.35s ease both",
        "pulse-dot": "pulseDot 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
