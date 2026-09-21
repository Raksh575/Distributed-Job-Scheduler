/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // support manual dark mode if needed
  theme: {
    extend: {
      colors: {
        background: "#05050A", // Extremely deep midnight for premium look
        foreground: "#f8fafc",
        card: {
          DEFAULT: "rgba(10, 12, 20, 0.7)", // Frosted glass card
          foreground: "#f8fafc",
          border: "rgba(255, 255, 255, 0.08)",
          hover: "rgba(255, 255, 255, 0.12)",
        },
        "card-border": "rgba(255, 255, 255, 0.08)",
        primary: {
          DEFAULT: "#4FACFE", // Electric Blue / Light Royal
          foreground: "#ffffff",
          hover: "#00F2FE", // Electric Blue
          glow: "rgba(79, 172, 254, 0.5)",
        },
        secondary: {
          DEFAULT: "#1A2980", // Deep Royal Blue / Navy
          foreground: "#e2e8f0",
          hover: "#26D0CE",
        },
        dark: {
          100: "#1e293b",
          200: "#0f172a",
          300: "#020617",
          pure: "#000000",
        },
        success: {
          DEFAULT: "#10b981", // Emerald
          glow: "rgba(16, 185, 129, 0.2)",
        },
        warning: {
          DEFAULT: "#f59e0b", // Amber
          glow: "rgba(245, 158, 11, 0.2)",
        },
        danger: {
          DEFAULT: "#f43f5e", // Rose Red
          glow: "rgba(244, 63, 94, 0.2)",
        },
        accent: {
          glow: "rgba(79, 172, 254, 0.15)",
          border: "rgba(79, 172, 254, 0.3)",
        }
      },
      fontFamily: {
        sans: ["'Plus Jakarta Sans'", "Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        "glass-sm": "0 2px 10px 0 rgba(0, 0, 0, 0.2), inset 0 1px 1px 0 rgba(255, 255, 255, 0.05)",
        "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.4), inset 0 1px 1px 0 rgba(255, 255, 255, 0.05)",
        "glass-lg": "0 12px 48px 0 rgba(0, 0, 0, 0.5), inset 0 1px 1px 0 rgba(255, 255, 255, 0.05)",
        "glow-primary": "0 0 20px rgba(79, 172, 254, 0.4)",
        "glow-success": "0 0 20px rgba(16, 185, 129, 0.4)",
        "glow-danger": "0 0 20px rgba(244, 63, 94, 0.4)",
      },
      backgroundImage: {
        "radial-dark": "radial-gradient(circle at top, #1e293b 0%, #05050A 100%)",
        "aurora": "radial-gradient(ellipse at top left, rgba(79, 172, 254, 0.15) 0%, transparent 40%), radial-gradient(ellipse at bottom right, rgba(0, 242, 254, 0.1) 0%, transparent 40%)",
        "mesh": "radial-gradient(at 0% 0%, rgba(79, 172, 254, 0.15) 0px, transparent 50%), radial-gradient(at 100% 0%, rgba(26, 41, 128, 0.15) 0px, transparent 50%)",
      },
      animation: {
        "pulse-slow": "pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "float": "float 6s ease-in-out infinite",
        "aurora-shift": "aurora 15s ease infinite",
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        aurora: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        }
      }
    },
  },
  plugins: [],
}
