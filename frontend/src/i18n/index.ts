import i18n from "i18next";
import { initReactI18next } from "react-i18next";

i18n.use(initReactI18next).init({
  lng: "zh",
  fallbackLng: "zh",
  resources: {
    zh: {
      translation: {
        title: "AQuantLens",
        subtitle: "AI 投研工作台",
      },
    },
    en: {
      translation: {
        title: "AQuantLens",
        subtitle: "AI Trading Research Workbench",
      },
    },
  },
});

export default i18n;
