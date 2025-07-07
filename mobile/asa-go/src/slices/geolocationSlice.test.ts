import geolocationSlice, {
  geolocationInitialState,
  setError,
  setPosition,
} from "@/slices/geolocationSlice";
import { Position } from "@capacitor/geolocation";

describe("geolocationSlice", () => {
  it("should handle setPosition", () => {
    const position = {
      coords: { latitude: 1, longitude: 2, accuracy: 10 },
      timestamp: 123456789,
    } as Position;

    const nextState = geolocationSlice(
      geolocationInitialState,
      setPosition(position)
    );
    expect(nextState.position).toEqual(position);
    expect(nextState.error).toBeNull();
  });

  it("should handle setError", () => {
    const error = "Permission denied";
    const nextState = geolocationSlice(
      geolocationInitialState,
      setError(error)
    );
    expect(nextState.error).toEqual(error);
    expect(nextState.position).toBeNull();
  });
});
