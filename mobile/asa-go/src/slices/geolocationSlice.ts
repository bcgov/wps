import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Position, Geolocation } from "@capacitor/geolocation";
import { AppDispatch, AppThunk } from "@/store";
import { DateTime } from "luxon";

export interface GeolocationState {
  position: Position | null;
  error: string | null;
  loading: boolean;
  permissionGranted: boolean;
  lastUpdated: string | null;
  watchId: string | null;
}

export const geolocationInitialState: GeolocationState = {
  position: null,
  error: null,
  loading: false,
  permissionGranted: false,
  lastUpdated: null,
  watchId: null,
};

const geolocationSlice = createSlice({
  name: "geolocation",
  initialState: geolocationInitialState,
  reducers: {
    getLocationStart(state: GeolocationState) {
      state.loading = true;
      state.error = null;
    },
    getLocationSuccess(
      state: GeolocationState,
      action: PayloadAction<Position>
    ) {
      state.loading = false;
      state.position = action.payload;
      state.error = null;
      state.permissionGranted = true;
      state.lastUpdated = DateTime.now().toISO();
    },
    getLocationFailed(state: GeolocationState, action: PayloadAction<string>) {
      state.loading = false;
      state.error = action.payload;
      state.permissionGranted = false;
    },
    setPermissionStatus(
      state: GeolocationState,
      action: PayloadAction<boolean>
    ) {
      state.permissionGranted = action.payload;
    },
    startWatching(state: GeolocationState, action: PayloadAction<string>) {
      state.watchId = action.payload;
      state.error = null;
      state.loading = false; // Stop loading when watch starts
    },
    stopWatching(state: GeolocationState) {
      state.watchId = null;
    },
    clearLocation(state: GeolocationState) {
      state.position = null;
      state.error = null;
      state.loading = false;
      state.lastUpdated = null;
      state.watchId = null;
    },
  },
});

export const {
  getLocationStart,
  getLocationSuccess,
  getLocationFailed,
  setPermissionStatus,
  startWatching,
  stopWatching,
  clearLocation,
} = geolocationSlice.actions;

export default geolocationSlice.reducer;

const ensureLocationPermission = async (
  dispatch: AppDispatch
): Promise<void> => {
  const permissions = await Geolocation.checkPermissions();

  if (permissions.location !== "granted") {
    const requestResult = await Geolocation.requestPermissions();
    if (requestResult.location !== "granted") {
      dispatch(setPermissionStatus(false));
      throw new Error("Location permission denied");
    }
  }

  dispatch(setPermissionStatus(true));
};

// location tracking
export const startLocationTracking =
  (): AppThunk => async (dispatch, getState) => {
    try {
      const state = getState();

      // If already watching, no need to start again
      if (state.geolocation.watchId) {
        return;
      }

      dispatch(getLocationStart());
      await ensureLocationPermission(dispatch);

      const watchId = await Geolocation.watchPosition(
        {
          enableHighAccuracy: true,
          timeout: 15000, // wait up to 15 seconds for a position
          maximumAge: 5000, // cache position for 5 seconds
        },
        (position, err) => {
          if (err) {
            console.error("Watch position error:", err);
            dispatch(getLocationFailed(err.message || "Location watch failed"));
            return;
          }

          if (position) {
            dispatch(getLocationSuccess(position));
          }
        }
      );

      dispatch(startWatching(watchId));
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to start location tracking";
      dispatch(getLocationFailed(errorMessage));
      console.error("Location tracking error:", err);
    }
  };

export const stopLocationTracking =
  (): AppThunk => async (dispatch, getState) => {
    const state = getState();
    if (state.geolocation.watchId) {
      await Geolocation.clearWatch({ id: state.geolocation.watchId });
      dispatch(stopWatching());
    }
  };
