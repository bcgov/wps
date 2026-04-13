import authenticateSlice from "@/slices/authenticationSlice";
import dataSlice from "@/slices/dataSlice";
import fireCentresSlice from "@/slices/fireCentresSlice";
import geolocationSlice from "@/slices/geolocationSlice";
import networkStatusSlice from "@/slices/networkStatusSlice";
import pushNotificationSlice from "@/slices/pushNotificationSlice";
import runParametersSlice from "@/slices/runParametersSlice";
import { combineReducers } from "@reduxjs/toolkit";
import settingsSlice from "@/slices/settingsSlice";

export const rootReducer = combineReducers({
  fireCentres: fireCentresSlice,
  networkStatus: networkStatusSlice,
  geolocation: geolocationSlice,
  runParameters: runParametersSlice,
  authentication: authenticateSlice,
  data: dataSlice,
  settings: settingsSlice,
  pushNotification: pushNotificationSlice,
});
