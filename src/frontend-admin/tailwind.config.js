/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  safelist: [
    'hidden',
    'flex',
    'block',
    'inline-flex',
    'sm:flex',
    'sm:hidden',
    'sm:block',
    'md:flex',
    'md:hidden',
    'md:block',
    'lg:flex',
    'lg:hidden',
  ],
  theme: { extend: {} },
  plugins: [],
};
