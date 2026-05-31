import type { SVGProps } from "react";
import {
  CleanIcon,
  LearnIcon,
  TechIcon,
  MoveIcon,
  HeartIcon,
  CalendarIcon,
} from "@/components/icons";

type IconComponent = (p: SVGProps<SVGSVGElement> & { size?: number }) => JSX.Element;

/** Maps a task vertical to its line icon. */
export const VERTICAL_ICON: Record<string, IconComponent> = {
  home: CleanIcon,
  learn: LearnIcon,
  tech: TechIcon,
  care: HeartIcon,
  move: MoveIcon,
  events: CalendarIcon,
};
