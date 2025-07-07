import { Position } from "@capacitor/geolocation";
import { Map, Overlay } from "ol";
import { fromLonLat } from "ol/proj";
import { useEffect, useRef, useState } from "react";

interface UserLocationIndicatorProps {
  map: Map | null;
  position: Position | null;
}

const UserLocationIndicator = ({
  map,
  position,
}: UserLocationIndicatorProps) => {
  const [overlay, setOverlay] = useState<Overlay | null>(null);
  const elementRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!map || !elementRef.current) return;

    const userLocationOverlay = new Overlay({
      element: elementRef.current,
      positioning: "center-center",
      stopEvent: false,
      className: "user-location-overlay",
    });

    map.addOverlay(userLocationOverlay);
    setOverlay(userLocationOverlay);

    return () => {
      map.removeOverlay(userLocationOverlay);
    };
  }, [map]);

  // update blue dot when location changes without centering map
  useEffect(() => {
    if (!overlay || !position) {
      if (overlay) {
        overlay.setPosition(undefined);
      }
      return;
    }

    const coords = fromLonLat([
      position.coords.longitude,
      position.coords.latitude,
    ]);

    overlay.setPosition(coords);
  }, [overlay, position]);

  return (
    <div
      ref={elementRef}
      style={{
        width: "20px",
        height: "20px",
        borderRadius: "50%",
        backgroundColor: "rgba(51, 153, 204, 0.8)",
        border: "3px solid white",
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        pointerEvents: "none",
        zIndex: 1000,
      }}
      data-testid="user-location-indicator"
    />
  );
};

export default UserLocationIndicator;
