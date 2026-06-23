import type { Config } from "tailwindcss";

/**
 * Moufida "Warm Autumn" palette — mirrors the desktop app (frontend/src/theme.ts)
 * so the landing page feels like a natural extension of the product.
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#F5EBDD", // Cream Beige
        surface: "#EDE0CE", // Warm Sand
        surfaceHigh: "#E3D3BE", // Deeper Sand
        border: "#CBBAA8", // Warm brown border
        ink: "#2C1E17", // Dark Espresso — body text
        muted: "#8B6E5A", // Warm brown muted
        primary: "#6F4E37", // Coffee Brown
        primaryDark: "#5A3D2B",
        accent: "#C96A2D", // Fallen Leaves Orange
        accentHover: "#D98A3A", // Autumn Gold
        success: "#2E7D32",
        warning: "#C86A00",
        error: "#B71C1C",
        info: "#1565C0",
      },
      fontFamily: {
        heading: ["var(--font-playfair)", "Georgia", "serif"],
        body: ["var(--font-jakarta)", "system-ui", "sans-serif"],
        pixel: ["var(--font-pixel)", "monospace"],
      },
      boxShadow: {
        card: "0 2px 16px rgba(111,78,55,0.07), 0 1px 4px rgba(111,78,55,0.04)",
        cardHover: "0 8px 32px rgba(111,78,55,0.13), 0 2px 8px rgba(111,78,55,0.07)",
        btn: "0 4px 16px rgba(111,78,55,0.28)",
        btnAccent: "0 6px 20px rgba(201,106,45,0.35)",
      },
      borderRadius: {
        xl: "16px",
        "2xl": "22px",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(201,106,45,0.55)" },
          "70%": { boxShadow: "0 0 0 12px rgba(201,106,45,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(201,106,45,0)" },
        },
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-8px)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.22,1,0.36,1) forwards",
        "pulse-ring": "pulse-ring 1.8s ease-out infinite",
        float: "float 5s ease-in-out infinite",
        shimmer: "shimmer 2.5s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
