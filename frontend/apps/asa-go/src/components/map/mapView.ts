import { Preferences } from "@capacitor/preferences";
import { Coordinate } from "ol/coordinate";

export interface MapViewState {
  zoom: number;
  center: Coordinate;
}

const MAP_VIEW_STATE_KEY = "asaGoMapView";

export const saveMapViewState = async (state: MapViewState): Promise<void> => {
  await Preferences.set({
    key: MAP_VIEW_STATE_KEY,
    value: JSON.stringify(state),
  });
};

export const loadMapViewState = async (): Promise<MapViewState | null> => {
  const result = await Preferences.get({ key: MAP_VIEW_STATE_KEY });
  if (!result.value) {
    return null;
  }
  try {
    return JSON.parse(result.value) as MapViewState;
  } catch {
    return null;
  }
};
