/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    '../../templates/**/*.html',
    '../../**/templates/**/*.html',
    '../../**/forms.py',
    '../../**/admin.py',
    '../../**/*.js',
  ],
  plugins: [
    require('@tailwindcss/typography'),
    require('@tailwindcss/forms'),
    require('@tailwindcss/aspect-ratio'),
    require('@tailwindcss/container-queries'),
    require('tailwind-scrollbar'),
    require('tailwindcss-animate'),
    require('tailwindcss-animated'),
    require('tailwindcss-debug-screens'),
    require('daisyui'),
  ],
  theme: {
    debugScreens: {
      position: ['bottom', 'left'],
    },
    extend: {
      colors: {
        primary: "#3B82F6",
        secondary: "#60A5FA",
        cta: "#F97316",
        background: "#F8FAFC",
        text: "#1E293B",
      },
      fontFamily: {
        sans: ['"Open Sans"', 'sans-serif'],
        heading: ['"Poppins"', 'sans-serif'],
      },
      animation: {
        "rainbow": "rainbow var(--speed, 2s) infinite linear",
        "shimmer-spin": "spin 2s linear infinite",
        "border-beam": "border-beam calc(var(--duration)*1s) infinite linear",
      },
      keyframes: {
        "rainbow": {
          "0%": { "background-position": "0%" },
          "100%": { "background-position": "200%" },
        },
        "border-beam": {
          "100%": { "offset-distance": "100%" },
        },
      },
    },
  },
  daisyui: {
    themes: [
      {
        light: {
          "color-scheme": "light",
          "base-100": "oklch(98.5% 0.002 247.8)", // Slate 50
          "base-200": "oklch(96% 0.003 264.5)",
          "base-300": "oklch(92% 0.006 264.5)",
          "base-content": "oklch(27% 0.03 256.8)", // Slate 800
          "primary": "oklch(62.7% 0.194 257.6)", // Blue 500
          "primary-content": "oklch(98% 0.01 257.6)",
          "secondary": "oklch(72.7% 0.15 257.6)", // Blue 400
          "secondary-content": "oklch(98% 0.01 257.6)",
          "accent": "oklch(69% 0.18 42.6)", // Orange 500
          "accent-content": "oklch(98% 0.01 42.6)",
          "neutral": "oklch(21% 0.034 264.7)", // Slate 900
          "neutral-content": "oklch(98% 0.002 247.8)",
          "info": "oklch(74% 0.16 232.661)",
          "info-content": "oklch(29% 0.066 243.157)",
          "success": "oklch(77% 0.152 181.912)",
          "success-content": "oklch(27% 0.046 192.524)",
          "warning": "oklch(79% 0.184 86.047)",
          "warning-content": "oklch(26% 0.079 36.259)",
          "error": "oklch(71% 0.202 349.761)",
          "error-content": "oklch(28% 0.109 3.907)",
          "--radius-selector": "0.5rem",
          "--radius-field": "0.5rem",
          "--radius-box": "0.5rem",
          "--size-selector": "0.25rem",
          "--size-field": "0.25rem",
          "--border": "1px",
          "--depth": "1",
          "--noise": "0",
        },
      },
      {
        dark: {
          "color-scheme": "dark",
          "base-100": "oklch(21% 0.034 264.7)", // Slate 900
          "base-200": "oklch(17% 0.03 264.7)",
          "base-300": "oklch(13% 0.02 267)",
          "base-content": "oklch(98.5% 0.002 247.8)", // Slate 50
          "primary": "oklch(62.7% 0.194 257.6)", // Blue 500
          "primary-content": "oklch(98% 0.01 257.6)",
          "secondary": "oklch(72.7% 0.15 257.6)", // Blue 400
          "secondary-content": "oklch(98% 0.01 257.6)",
          "accent": "oklch(69% 0.18 42.6)", // Orange 500
          "accent-content": "oklch(98% 0.01 42.6)",
          "neutral": "oklch(98.5% 0.002 247.8)", // Slate 50 (Inverted)
          "neutral-content": "oklch(21% 0.034 264.7)",
          "info": "oklch(74% 0.16 232.661)",
          "info-content": "oklch(29% 0.066 243.157)",
          "success": "oklch(77% 0.152 181.912)",
          "success-content": "oklch(27% 0.046 192.524)",
          "warning": "oklch(79% 0.184 86.047)",
          "warning-content": "oklch(26% 0.079 36.259)",
          "error": "oklch(71% 0.202 349.761)",
          "error-content": "oklch(28% 0.109 3.907)",
          "--radius-selector": "0.5rem",
          "--radius-field": "0.5rem",
          "--radius-box": "0.5rem",
          "--size-selector": "0.25rem",
          "--size-field": "0.25rem",
          "--border": "1px",
          "--depth": "1",
          "--noise": "0",
        },
      },
    ],
    logs: false,
  },
}
