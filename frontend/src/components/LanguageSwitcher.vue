<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const languages = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' }
]

const changeLanguage = (e: Event) => {
  const target = e.target as HTMLSelectElement
  locale.value = target.value
}
</script>

<template>
  <div class="language-switcher">
    <select :value="locale" @change="changeLanguage" class="lang-select glass">
      <option v-for="lang in languages" :key="lang.code" :value="lang.code">
        {{ lang.flag }} {{ lang.name }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.language-switcher {
  /* Layout managed by parent container */
}

.lang-select {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--glass-border);
  font-size: 0.9rem;
  cursor: pointer;
  appearance: none;
  padding-right: 2rem;
  background-image: var(--select-arrow);
  background-repeat: no-repeat;
  background-position: right 0.7rem top 50%;
  background-size: 0.65rem auto;
}

.lang-select:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.lang-select option {
  background: var(--bg-primary);
  color: var(--text-primary);
}
</style>
