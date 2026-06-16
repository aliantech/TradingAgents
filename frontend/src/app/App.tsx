import { useTranslation } from "react-i18next";

export function App() {
  const { t, i18n } = useTranslation();

  return (
    <main>
      <h1>{t("title")}</h1>
      <p>{t("subtitle")}</p>
      <button type="button" onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}>
        {i18n.language === "zh" ? "English" : "中文"}
      </button>
    </main>
  );
}
