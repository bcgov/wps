// store/geolocationSlice.ts
import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Position } from "@capacitor/geolocation";

interface GeolocationState {
  position: Position | null;
  error: string | null;
  watching: boolean;
}

export const geolocationInitialState: GeolocationState = {
  position: null,
  error: null,
  watching: false,
};

const geolocationSlice = createSlice({
  name: "geolocation",
  initialState: geolocationInitialState,
  reducers: {
    setPosition(state, action: PayloadAction<Position>) {
      state.position = action.payload;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
    },
    setWatching(state, action: PayloadAction<boolean>) {
      state.watching = action.payload;
    },
  },
});

export const { setPosition, setError, setWatching } = geolocationSlice.actions;
export default geolocationSlice.reducer;
