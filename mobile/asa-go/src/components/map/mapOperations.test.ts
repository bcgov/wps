import { describe, it, expect } from "vitest";
import { findFireZoneForLocation } from "./mapOperations";
import { Position } from "@capacitor/geolocation";

describe("findFireZoneForLocation", () => {
  it("returns the correct zoneId when user is inside a fire zone", () => {
    const userPosition = {
      coords: { latitude: 50.67, longitude: -120.34 }, // Kamloops coords
      timestamp: 123456789,
    } as Position;

    const result = findFireZoneForLocation(userPosition);
    expect(result).toBe("16"); // Kamloops Fire Zone
  });

  it("returns the correct zoneId when user is inside another fire zone", () => {
    const userPosition = {
      coords: { latitude: 50.26, longitude: -119.27 }, // Vernon coords
      timestamp: 123456789,
    } as Position;

    const result = findFireZoneForLocation(userPosition);
    expect(result).toBe("10"); // Vernon Fire Zone
  });

  it("returns null when user is not in any fire zone", () => {
    const userPosition = {
      coords: { latitude: 0, longitude: 0 }, // Vernon coords
      timestamp: 123456789,
    } as Position;

    const result = findFireZoneForLocation(userPosition);
    expect(result).toBeNull();
  });
});
