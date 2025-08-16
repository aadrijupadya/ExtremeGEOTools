export function usePersistentDraft(storageKey, ttlMs = 7 * 24 * 60 * 60 * 1000) {
  const loadDraft = () => {
    try {
      const raw = localStorage.getItem(storageKey);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const savedAt = Number(parsed?.savedAt || 0);
      if (!savedAt || Date.now() - savedAt > ttlMs) {
        localStorage.removeItem(storageKey);
        return null;
      }
      return parsed?.data || null;
    } catch (_) {
      return null;
    }
  };

  const saveDraft = (data) => {
    try {
      const payload = { data, savedAt: Date.now() };
      localStorage.setItem(storageKey, JSON.stringify(payload));
    } catch (_) {
      // ignore storage errors
    }
  };

  const clearDraft = () => {
    try {
      localStorage.removeItem(storageKey);
    } catch (_) {
      // ignore
    }
  };

  return { loadDraft, saveDraft, clearDraft };
}


