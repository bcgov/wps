import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { ConnectionStatus } from "@capacitor/network"


export interface NetworkStatusState {
  networkStatus: ConnectionStatus
}

const initialState: NetworkStatusState = {
  networkStatus: { connected: false, connectionType: 'none'},
};

const networkStatusSlice = createSlice({
  name: "networkStatus",
  initialState,
  reducers: {
    updateNetworkStatus(state: NetworkStatusState, action: PayloadAction<ConnectionStatus>) {
      state.networkStatus = action.payload
    },
  },
});

export const { updateNetworkStatus } =
networkStatusSlice.actions;

export default networkStatusSlice.reducer;
