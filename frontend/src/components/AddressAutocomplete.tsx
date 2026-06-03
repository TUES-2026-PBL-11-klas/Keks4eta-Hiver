import { useEffect, useRef } from "react";
import { useMapsLibrary } from "@vis.gl/react-google-maps";

export interface PlacePick {
  /** Human-readable address to store as location_display. */
  display: string;
  latitude: number | null;
  longitude: number | null;
}

interface Props {
  id?: string;
  className?: string;
  placeholder?: string;
  /** Current text value (controlled by the parent). */
  value: string;
  /** Fired on every keystroke — parent should clear any stored coords. */
  onChange: (text: string) => void;
  /** Fired when the user picks a suggestion — carries the address + coords. */
  onPick: (pick: PlacePick) => void;
}

/**
 * Address field backed by Google Places Autocomplete. Must be rendered inside an
 * <APIProvider>. The parent owns the text value; picking a suggestion also yields
 * coordinates so the task can be stored with a real PostGIS point.
 */
export function AddressAutocomplete({ id, className, placeholder, value, onChange, onPick }: Props) {
  const places = useMapsLibrary("places");
  const inputRef = useRef<HTMLInputElement>(null);
  const widgetRef = useRef<google.maps.places.Autocomplete | null>(null);
  // Keep the latest onPick without re-creating the widget (avoids stale closures).
  const onPickRef = useRef(onPick);
  onPickRef.current = onPick;

  useEffect(() => {
    if (!places || !inputRef.current || widgetRef.current) return;
    const widget = new places.Autocomplete(inputRef.current, {
      fields: ["formatted_address", "geometry", "name"],
    });
    widgetRef.current = widget;
    const listener = widget.addListener("place_changed", () => {
      const place = widget.getPlace();
      const loc = place.geometry?.location;
      onPickRef.current({
        display: place.formatted_address ?? place.name ?? inputRef.current?.value ?? "",
        latitude: loc ? loc.lat() : null,
        longitude: loc ? loc.lng() : null,
      });
    });
    return () => listener.remove();
  }, [places]);

  return (
    <input
      id={id}
      ref={inputRef}
      className={className}
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      autoComplete="off"
    />
  );
}
