import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { Position } from "@capacitor/geolocation";

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
    setPosition(state, action: PayloadAction<Position>) {
      console.log("Updating position:", action.payload);
      state.position = action.payload;
      state.loading = false;
    },
    setError(state, action: PayloadAction<string | null>) {
      state.error = action.payload;
      state.loading = false;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
  },
});

export const { setPosition, setError, setLoading } = geolocationSlice.actions;
export default geolocationSlice.reducer;
