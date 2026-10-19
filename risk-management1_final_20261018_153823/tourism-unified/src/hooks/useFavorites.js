import { useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "sj_favorite_sites";

function readFavorites() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (e) {
    return [];
  }
}

export function useFavorites() {
  const [favorites, setFavorites] = useState(readFavorites);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(favorites));
    } catch (e) {
      // localStorage unavailable (private browsing, quota) -- fail silently, UI still works in-session
    }
  }, [favorites]);

  const isFavorite = useCallback((siteId) => favorites.includes(siteId), [favorites]);

  const toggleFavorite = useCallback((siteId) => {
    setFavorites((prev) =>
      prev.includes(siteId) ? prev.filter((id) => id !== siteId) : [...prev, siteId]
    );
  }, []);

  return { favorites, isFavorite, toggleFavorite };
}
