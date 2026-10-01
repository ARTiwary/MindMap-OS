/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: "#0B0C10",
          light: "#FAFAF8",
        },
        surface: {
          DEFAULT: "#14161C",
          light: "#FFFFFF",
        },
        border: {
          DEFAULT: "#22252E",
          light: "#E7E5DE",
        },
        accent: {
          DEFAULT: "#7C8CFF",
          soft: "#AEB8FF",
          dim: "#4A50A8",
        },
        node: {
          idea: "#F5B95C",
          note: "#7C8CFF",
          concept: "#5CD6C0",
          question: "#F27878",
          resource: "#B98CE8",
          project: "#5CC2F2",
          book: "#E89A5C",
          course: "#8CD65C",
          person: "#F28CC5",
          topic: "#5C9DE8",
          reference: "#A0A8B8",
        },
      },
      fontFamily: {
        display: ["'Fraunces'", "serif"],
        sans: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        xl2: "1.25rem",
      },
    },
  },
  plugins: [],
};
