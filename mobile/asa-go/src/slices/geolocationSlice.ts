import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Position, Geolocation } from "@capacitor/geolocation";
import { AppDispatch } from "@/store";

interface GeolocationState {
  position: Position | null;
  error: string | null;
}

export const geolocationInitialState: GeolocationState = {
  position: null,
  error: null,
};

const geolocationSlice = createSlice({
  name: "geolocation",
  initialState: geolocationInitialState,
  reducers: {
    setPosition(state, action: PayloadAction<Position>) {
      state.position = action.payload;
      state.error = null; // clear error on successful position update
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
  },
});

export const { setPosition, setError } = geolocationSlice.actions;
export default geolocationSlice.reducer;

// Store the watch ID
let watchId: string | null = null;

export const startWatchingLocation = () => async (dispatch: AppDispatch) => {
  dispatch(setError(null)); // Clear any previous errors
  try {
    const permStatus = await Geolocation.checkPermissions();
    if (permStatus.location !== "granted") {
      const req = await Geolocation.requestPermissions();
      if (req.location !== "granted") {
        dispatch(setError("Location permission denied"));
        return;
      }
    }

    // Clear previous watch if it exists so we don't start multiple watches
    if (watchId) {
      await Geolocation.clearWatch({ id: watchId });
      watchId = null;
    }

    // Start watching position
    watchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true, timeout: 60000 },
      (pos, err) => {
        if (err) {
          dispatch(setError(err.message));
        } else if (pos) {
          dispatch(setPosition(pos));
        }
      }
    );
  } catch (e) {
    dispatch(setError((e as Error).message));
  }
};

export const stopWatchingLocation = () => async () => {
  if (watchId) {
    await Geolocation.clearWatch({ id: watchId });
    watchId = null;
  }
};
