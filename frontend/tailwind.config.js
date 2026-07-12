/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#E7E9E4",       // page background: cool sage paper, not warm cream
        card: "#FBFBF9",        // evidence card / answer card surface
        ink: "#1F2A24",         // primary text: deep forest-black
        "ink-muted": "#5B6259", // secondary text
        tab: "#B08D2E",         // citation index-tab accent (mustard/ochre)
        "tab-soft": "#F1E6C8",  // citation tab background tint
        grounded: "#3B6E4E",    // moss green: fully-grounded status
        "grounded-soft": "#DCE8DE",
        rejected: "#A63B32",    // muted brick: rejected/ungrounded status
        "rejected-soft": "#F1DCDA",
        rule: "#C9CDC3",        // hairline dividers
      },
      fontFamily: {
        display: ['var(--font-display)', "Georgia", "serif"],
        sans: ['var(--font-sans)', "system-ui", "sans-serif"],
        mono: ['var(--font-mono)', "ui-monospace", "monospace"],
      },
      borderRadius: {
        card: "2px", // near-flat, index-card edges rather than soft app-UI corners
      },
      keyframes: {
        flash: {
          "0%": { backgroundColor: "#F1E6C8" },
          "100%": { backgroundColor: "transparent" },
        },
      },
      animation: {
        flash: "flash 1.4s ease-out",
      },
    },
  },
  plugins: [],
};
