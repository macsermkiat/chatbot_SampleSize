import { useLocale } from "./context";

export function useTranslation(namespace: string) {
  const { t, locale, setLocale } = useLocale();

  return {
    t: (key: string) => t(namespace, key),
    locale,
    setLocale,
  };
}
