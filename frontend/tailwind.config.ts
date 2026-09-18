import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F8F5",
        primary: "#2F7064",
        ink: "#172522",
        muted: "#5F6F6B",
        danger: "#C2413B",
        line: "#D8E1DD"
      },
      borderRadius: {
        card: "24px"
      },
      boxShadow: {
        soft: "0 24px 70px rgba(23, 37, 34, 0.10)",
        panel: "0 16px 40px rgba(47, 112, 100, 0.13)"
      }
    }
  },
  plugins: []
} satisfies Config;
