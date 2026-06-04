import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { favoriteService } from "@/lib/services";
import { useAuth } from "@/context/AuthContext";
import type { FavoriteTarget } from "@/types";

interface FavoritesContextValue {
  /** True if the given target is currently saved by the user. */
  isFavorited: (type: FavoriteTarget, id: string) => boolean;
  /** Optimistically toggle a save; reverts on failure. No-op when signed out. */
  toggle: (type: FavoriteTarget, id: string) => Promise<void>;
  refresh: () => Promise<void>;
}

const FavoritesContext = createContext<FavoritesContextValue | null>(null);

export function FavoritesProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [taskIds, setTaskIds] = useState<Set<string>>(new Set());
  const [hiverIds, setHiverIds] = useState<Set<string>>(new Set());

  const setFor = useCallback(
    (type: FavoriteTarget) => (type === "task" ? setTaskIds : setHiverIds),
    [],
  );

  const refresh = useCallback(async () => {
    if (!isAuthenticated) {
      setTaskIds(new Set());
      setHiverIds(new Set());
      return;
    }
    try {
      const ids = await favoriteService.ids();
      setTaskIds(new Set(ids.tasks));
      setHiverIds(new Set(ids.hivers));
    } catch {
      // Non-fatal — hearts just render empty until the next successful load.
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const isFavorited = useCallback(
    (type: FavoriteTarget, id: string) =>
      (type === "task" ? taskIds : hiverIds).has(id),
    [taskIds, hiverIds],
  );

  const toggle = useCallback(
    async (type: FavoriteTarget, id: string) => {
      if (!isAuthenticated) return;
      const set = type === "task" ? taskIds : hiverIds;
      const wasSaved = set.has(id);
      // Optimistic update.
      setFor(type)((prev) => {
        const next = new Set(prev);
        if (wasSaved) next.delete(id);
        else next.add(id);
        return next;
      });
      try {
        if (wasSaved) await favoriteService.remove(type, id);
        else await favoriteService.add(type, id);
      } catch {
        // Revert on failure.
        setFor(type)((prev) => {
          const next = new Set(prev);
          if (wasSaved) next.add(id);
          else next.delete(id);
          return next;
        });
      }
    },
    [isAuthenticated, taskIds, hiverIds, setFor],
  );

  const value = useMemo<FavoritesContextValue>(
    () => ({ isFavorited, toggle, refresh }),
    [isFavorited, toggle, refresh],
  );

  return <FavoritesContext.Provider value={value}>{children}</FavoritesContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useFavorites(): FavoritesContextValue {
  const ctx = useContext(FavoritesContext);
  if (!ctx) throw new Error("useFavorites must be used within <FavoritesProvider>");
  return ctx;
}
