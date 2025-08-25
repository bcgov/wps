import authenticateSlice from "@/slices/authenticationSlice";
import dataSlice from "@/slices/dataSlice";
import fireCentersSlice from "@/slices/fireCentersSlice";
import geolocationSlice from "@/slices/geolocationSlice";
import networkStatusSlice from "@/slices/networkStatusSlice";
import runParametersSlice from "@/slices/runParametersSlice";
import { combineReducers } from "@reduxjs/toolkit";

export const rootReducer = combineReducers({
  fireCenters: fireCentersSlice,
  networkStatus: networkStatusSlice,
  geolocation: geolocationSlice,
  runParameters: runParametersSlice,
  authentication: authenticateSlice,
  data: dataSlice,
});
