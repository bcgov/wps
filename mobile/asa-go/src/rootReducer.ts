import authenticateSlice from "@/slices/authenticationSlice";
import dataSlice from "@/slices/dataSlice";
import fireCentersSlice from "@/slices/fireCentersSlice";
import fireCentreHFIFuelStatsSlice from "@/slices/fireCentreHFIFuelStatsSlice";
import fireCentreTPIStatsSlice from "@/slices/fireCentreTPIStatsSlice";
import fireShapeAreasSlice from "@/slices/fireZoneAreasSlice";
import fireZoneElevationInfoSlice from "@/slices/fireZoneElevationInfoSlice";
import geolocationSlice from "@/slices/geolocationSlice";
import networkStatusSlice from "@/slices/networkStatusSlice";
import provincialSummarySlice from "@/slices/provincialSummarySlice";
import runParametersSlice from "@/slices/runParametersSlice";
import { combineReducers } from "@reduxjs/toolkit";

export const rootReducer = combineReducers({
  fireCenters: fireCentersSlice,
  provincialSummary: provincialSummarySlice,
  fireZoneElevationInfo: fireZoneElevationInfoSlice,
  fireShapeAreas: fireShapeAreasSlice,
  fireCentreTPIStats: fireCentreTPIStatsSlice,
  fireCentreHFIFuelStats: fireCentreHFIFuelStatsSlice,
  networkStatus: networkStatusSlice,
  geolocation: geolocationSlice,
  runParameters: runParametersSlice,
  authentication: authenticateSlice,
  data: dataSlice,
});
