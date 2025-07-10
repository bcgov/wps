import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Position, Geolocation } from "@capacitor/geolocation";
import { AppDispatch } from "@/store";

interface GeolocationState {
  position: Position | null;
  error: string | null;
  loading: boolean;
}

export const geolocationInitialState: GeolocationState = {
  position: null,
  error: null,
  loading: false,
};

const geolocationSlice = createSlice({
  name: "geolocation",
  initialState: geolocationInitialState,
  reducers: {
    setPosition(state, action: PayloadAction<Position | null>) {
      state.position = action.payload;
      // Only clear error if we have a valid position
      if (action.payload) {
        state.error = null;
      }
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    setLoading(state, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    },
  },
});

export const { setPosition, setError, setLoading } = geolocationSlice.actions;
export default geolocationSlice.reducer;

// Store the watch ID
let watchId: string | null = null;

export const startWatchingLocation = () => async (dispatch: AppDispatch) => {
  dispatch(stopWatchingLocation()); // clear previous watch so we don't start multiple watches
  try {
    const permStatus = await Geolocation.checkPermissions();
    if (permStatus.location !== "granted") {
      const req = await Geolocation.requestPermissions();
      if (req.location !== "granted") {
        dispatch(setError("Location permission denied"));
        dispatch(setPosition(null));
        return;
      }
    }

    dispatch(setLoading(true));
    // we can't set a loading state or maintain an error state while trying to find a position
    // with watchPosition, so we first get the current position
    const pos = await Geolocation.getCurrentPosition({
      enableHighAccuracy: true,
      timeout: 20000, // give it 20 seconds to find a position
    });
    dispatch(setPosition(pos));
    dispatch(setLoading(false));

    // start watching position
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
    dispatch(setLoading(false));
  }
};

export const stopWatchingLocation = () => async () => {
  if (watchId) {
    await Geolocation.clearWatch({ id: watchId });
    watchId = null;
  }
};
