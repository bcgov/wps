import { fireZoneExtentsMap } from "@/fireZoneUnitExtents";
import { Position } from "@capacitor/geolocation";
import { fromLonLat } from "ol/proj";

export const findFireZoneForLocation = (userPosition: Position) => {
  const userCoords = fromLonLat([
    userPosition.coords.longitude,
    userPosition.coords.latitude,
  ]);

  // find fire zone for user coords
  for (const [zoneId, extent] of fireZoneExtentsMap.entries()) {
    const [minX, minY, maxX, maxY] = extent;

    if (
      userCoords[0] >= minX &&
      userCoords[0] <= maxX &&
      userCoords[1] >= minY &&
      userCoords[1] <= maxY
    ) {
      return zoneId;
    }
  }

  return null; // user isn't in any fire zone
};
