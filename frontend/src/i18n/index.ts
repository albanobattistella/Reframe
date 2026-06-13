import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import de from './locales/de.json'
import es from './locales/es.json'
import fr from './locales/fr.json'

const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: navigator.language.split('-')[0] || 'en', // default locale
  fallbackLocale: 'en',
  messages: {
    en,
    de,
    es,
    fr
  }
})

export default i18n
