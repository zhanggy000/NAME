import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        wuxing: {
          mu:  "#10b981", // 木
          huo: "#ef4444", // 火
          tu:  "#d97706", // 土
          jin: "#eab308", // 金
          shui: "#3b82f6", // 水
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', '"Source Han Serif"', "serif"],
      },
    },
  },
  plugins: [],
};
export default config;
