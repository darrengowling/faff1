import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { translations } from './translations';

const resources = {
  en: {
    translation: translations
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'en', // Default language
    fallbackLng: 'en',
    
    interpolation: {
      escapeValue: false // React already escapes values
    },
    
    // Key separator for nested keys
    keySeparator: '.',
    
    // Namespace separator
    nsSeparator: ':',
    
    debug: process.env.NODE_ENV === 'development'
  });

export default i18n;