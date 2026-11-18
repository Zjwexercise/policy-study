import { ref } from 'vue';

const THEME_KEY = 'policy_theme';

const savedTheme = localStorage.getItem(THEME_KEY);
const prefersDark = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

export const isDark = ref(initialDark);

export function applyTheme(dark) {
  isDark.value = dark;
  if (typeof document !== 'undefined') {
    const root = document.documentElement;
    const body = document.body;
    if (dark) {
      root.classList.add('dark');
      body.classList.add('dark');
      localStorage.setItem(THEME_KEY, 'dark');
    } else {
      root.classList.remove('dark');
      body.classList.remove('dark');
      localStorage.setItem(THEME_KEY, 'light');
    }
  }
}

export function toggleTheme() {
  applyTheme(!isDark.value);
}

export function initTheme() {
  applyTheme(isDark.value);
}
