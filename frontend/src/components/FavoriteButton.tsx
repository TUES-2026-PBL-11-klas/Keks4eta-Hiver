import { type MouseEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";
import { ROUTES } from "@/constants/routes";
import { HeartIcon } from "@/components/icons";
import type { FavoriteTarget } from "@/types";
import s from "./FavoriteButton.module.css";

const cx = (...c: (string | false | undefined)[]) => c.filter(Boolean).join(" ");

/**
 * Heart toggle for saving a task or hiver. Stops click propagation so it works
 * inside a card that is itself a link; signed-out users are sent to login.
 */
export function FavoriteButton({
  type,
  id,
  size = 18,
  className,
}: {
  type: FavoriteTarget;
  id: string;
  size?: number;
  className?: string;
}) {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { isFavorited, toggle } = useFavorites();
  const saved = isFavorited(type, id);

  function onClick(e: MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN);
      return;
    }
    void toggle(type, id);
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={saved}
      aria-label={saved ? "Remove from saved" : "Save"}
      className={cx(s.btn, saved && s.on, className)}
    >
      <HeartIcon size={size} fill={saved ? "currentColor" : "none"} />
    </button>
  );
}
